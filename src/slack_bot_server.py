"""Slack bot server for document scanning via slash commands and file uploads."""

import hashlib
import hmac
import json
import os
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional
from dataclasses import dataclass

from .document_scanner import DocumentScanner, ScanResult, format_scan_result_for_slack


@dataclass
class SlackRequest:
    """Parsed Slack request data."""
    command: Optional[str] = None
    text: Optional[str] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None
    response_url: Optional[str] = None
    trigger_id: Optional[str] = None
    file_id: Optional[str] = None
    file_url: Optional[str] = None


class SlackBotServer:
    """Server for handling Slack slash commands and file uploads for document scanning."""

    def __init__(
        self,
        slack_bot_token: str,
        slack_signing_secret: str,
        anthropic_api_key: str,
        webhook_url: Optional[str] = None
    ):
        """Initialize the Slack bot server.

        Args:
            slack_bot_token: Slack Bot User OAuth Token (xoxb-...)
            slack_signing_secret: Slack App signing secret for request verification
            anthropic_api_key: Anthropic API key for Claude Vision
            webhook_url: Optional webhook URL for sending messages
        """
        self.bot_token = slack_bot_token
        self.signing_secret = slack_signing_secret
        self.webhook_url = webhook_url
        self.scanner = DocumentScanner(anthropic_api_key)

    def verify_slack_signature(self, timestamp: str, body: str, signature: str) -> bool:
        """Verify that a request came from Slack.

        Args:
            timestamp: X-Slack-Request-Timestamp header
            body: Raw request body
            signature: X-Slack-Signature header

        Returns:
            True if signature is valid
        """
        # Prevent replay attacks
        if abs(time.time() - int(timestamp)) > 60 * 5:
            return False

        sig_basestring = f"v0:{timestamp}:{body}"
        computed_signature = "v0=" + hmac.new(
            self.signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(computed_signature, signature)

    def parse_slash_command(self, body: str) -> SlackRequest:
        """Parse Slack slash command request body.

        Args:
            body: URL-encoded request body

        Returns:
            SlackRequest with parsed data
        """
        params = urllib.parse.parse_qs(body)

        return SlackRequest(
            command=params.get("command", [None])[0],
            text=params.get("text", [""])[0],
            user_id=params.get("user_id", [None])[0],
            user_name=params.get("user_name", [None])[0],
            channel_id=params.get("channel_id", [None])[0],
            channel_name=params.get("channel_name", [None])[0],
            response_url=params.get("response_url", [None])[0],
            trigger_id=params.get("trigger_id", [None])[0]
        )

    def parse_event(self, body: str) -> dict:
        """Parse Slack event payload.

        Args:
            body: JSON request body

        Returns:
            Parsed event data
        """
        return json.loads(body)

    def download_file(self, file_url: str) -> tuple[bytes, str]:
        """Download a file from Slack.

        Args:
            file_url: Slack file URL (url_private or url_private_download)

        Returns:
            Tuple of (file_bytes, content_type)
        """
        req = urllib.request.Request(
            file_url,
            headers={"Authorization": f"Bearer {self.bot_token}"}
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                content_type = response.headers.get("Content-Type", "image/jpeg")
                return response.read(), content_type
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Failed to download file: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to connect: {e.reason}")

    def get_file_info(self, file_id: str) -> dict:
        """Get file info from Slack API.

        Args:
            file_id: Slack file ID

        Returns:
            File info dict
        """
        url = f"https://slack.com/api/files.info?file={file_id}"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {self.bot_token}"}
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                if not result.get("ok"):
                    raise RuntimeError(f"Slack API error: {result.get('error')}")
                return result.get("file", {})
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Failed to get file info: {e.code}")

    def send_response(self, response_url: str, message: dict, replace_original: bool = False):
        """Send a response to Slack via response_url.

        Args:
            response_url: Slack response URL
            message: Message payload (text, blocks, etc.)
            replace_original: Whether to replace the original message
        """
        payload = {**message}
        if replace_original:
            payload["replace_original"] = True

        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            response_url,
            data=data,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            print(f"Failed to send response: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            print(f"Failed to connect: {e.reason}")

    def send_webhook_message(self, message: dict):
        """Send a message via webhook URL.

        Args:
            message: Message payload
        """
        if not self.webhook_url:
            return

        data = json.dumps(message).encode("utf-8")

        req = urllib.request.Request(
            self.webhook_url,
            data=data,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read()
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            print(f"Webhook error: {e}")

    def post_message(self, channel: str, message: dict):
        """Post a message to a Slack channel.

        Args:
            channel: Channel ID
            message: Message payload (text, blocks, etc.)
        """
        url = "https://slack.com/api/chat.postMessage"
        payload = {"channel": channel, **message}

        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.bot_token}"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                if not result.get("ok"):
                    print(f"Slack API error: {result.get('error')}")
                return result
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            print(f"Failed to post message: {e}")

    def handle_scan_command(self, request: SlackRequest) -> dict:
        """Handle /scan slash command.

        Args:
            request: Parsed slash command request

        Returns:
            Immediate response dict
        """
        # Check if a file URL was provided in the command text
        text = request.text or ""

        if not text.strip():
            return {
                "response_type": "ephemeral",
                "text": "Please provide a file URL or upload a file with the /scan command.\n\nUsage:\n- `/scan <file_url>` - Scan a document from URL\n- Upload a file and use `/scan` in the message"
            }

        # Check if it looks like a URL
        if text.startswith("http"):
            # Return acknowledgment, process in background
            return {
                "response_type": "in_channel",
                "text": f":hourglass_flowing_sand: Scanning document... Please wait."
            }

        return {
            "response_type": "ephemeral",
            "text": f"I'll scan the document you provided. Processing..."
        }

    def process_scan(self, file_url: str, response_url: str, channel_id: str, user_name: str):
        """Process a document scan request.

        Args:
            file_url: URL of the file to scan
            response_url: Slack response URL for sending results
            channel_id: Channel ID for posting results
            user_name: Name of user who requested scan
        """
        try:
            # Download file
            file_bytes, content_type = self.download_file(file_url)

            # Map content type to media type
            media_type = content_type.split(";")[0].strip()
            if media_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
                media_type = "image/jpeg"

            # Scan document
            result = self.scanner.scan_bytes(file_bytes, media_type)

            # Format response
            slack_message = format_scan_result_for_slack(result)

            # Add user context
            slack_message["blocks"].insert(0, {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f":page_facing_up: Document scanned by @{user_name}"
                    }
                ]
            })

            # Send response
            if response_url:
                self.send_response(response_url, slack_message)

        except Exception as e:
            error_message = {
                "response_type": "in_channel",
                "text": f":x: Scan failed: {str(e)}"
            }
            if response_url:
                self.send_response(response_url, error_message)

    def handle_file_shared(self, event: dict) -> Optional[dict]:
        """Handle file_shared event.

        Args:
            event: Slack event data

        Returns:
            Response dict or None
        """
        file_id = event.get("file_id")
        channel_id = event.get("channel_id")
        user_id = event.get("user_id")

        if not file_id:
            return None

        # Get file info
        try:
            file_info = self.get_file_info(file_id)
        except Exception as e:
            print(f"Failed to get file info: {e}")
            return None

        # Check if it's an image
        mimetype = file_info.get("mimetype", "")
        if not mimetype.startswith("image/"):
            return None

        file_url = file_info.get("url_private_download") or file_info.get("url_private")
        if not file_url:
            return None

        # Download and scan
        try:
            file_bytes, content_type = self.download_file(file_url)
            result = self.scanner.scan_bytes(file_bytes, mimetype)

            # Format and send response
            slack_message = format_scan_result_for_slack(result)

            # Post to channel
            self.post_message(channel_id, slack_message)

            return {"ok": True}

        except Exception as e:
            print(f"Scan error: {e}")
            self.post_message(channel_id, {"text": f":x: Failed to scan document: {str(e)}"})
            return None


def create_flask_app(server: SlackBotServer):
    """Create Flask app for the Slack bot.

    Args:
        server: SlackBotServer instance

    Returns:
        Flask app
    """
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        raise ImportError("Flask is required. Install with: pip install flask")

    app = Flask(__name__)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "healthy"})

    @app.route("/slack/commands", methods=["POST"])
    def handle_command():
        """Handle Slack slash commands."""
        # Verify request
        timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
        signature = request.headers.get("X-Slack-Signature", "")
        body = request.get_data(as_text=True)

        if not server.verify_slack_signature(timestamp, body, signature):
            return jsonify({"error": "Invalid signature"}), 401

        # Parse command
        slack_request = server.parse_slash_command(body)

        if slack_request.command == "/scan":
            # Return immediate response
            response = server.handle_scan_command(slack_request)

            # Process scan in background if URL provided
            text = slack_request.text or ""
            if text.startswith("http"):
                import threading
                thread = threading.Thread(
                    target=server.process_scan,
                    args=(text, slack_request.response_url, slack_request.channel_id, slack_request.user_name)
                )
                thread.start()

            return jsonify(response)

        return jsonify({"text": "Unknown command"})

    @app.route("/slack/events", methods=["POST"])
    def handle_event():
        """Handle Slack events."""
        # Verify request
        timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
        signature = request.headers.get("X-Slack-Signature", "")
        body = request.get_data(as_text=True)

        if not server.verify_slack_signature(timestamp, body, signature):
            return jsonify({"error": "Invalid signature"}), 401

        data = json.loads(body)

        # Handle URL verification challenge
        if data.get("type") == "url_verification":
            return jsonify({"challenge": data.get("challenge")})

        # Handle events
        event = data.get("event", {})
        event_type = event.get("type")

        if event_type == "file_shared":
            # Process in background
            import threading
            thread = threading.Thread(
                target=server.handle_file_shared,
                args=(event,)
            )
            thread.start()

        return jsonify({"ok": True})

    return app


def run_server(host: str = "0.0.0.0", port: int = 3000):
    """Run the Slack bot server.

    Args:
        host: Host to bind to
        port: Port to listen on
    """
    from dotenv import load_dotenv
    load_dotenv()

    # Load configuration
    bot_token = os.environ.get("SLACK_BOT_TOKEN")
    signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")

    if not bot_token:
        raise ValueError("SLACK_BOT_TOKEN environment variable required")
    if not signing_secret:
        raise ValueError("SLACK_SIGNING_SECRET environment variable required")
    if not anthropic_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable required")

    # Create server
    server = SlackBotServer(
        slack_bot_token=bot_token,
        slack_signing_secret=signing_secret,
        anthropic_api_key=anthropic_key,
        webhook_url=webhook_url
    )

    # Create and run Flask app
    app = create_flask_app(server)

    print(f"\n{'='*50}")
    print("Foliox Document Scanner Bot")
    print(f"{'='*50}")
    print(f"Server running on http://{host}:{port}")
    print(f"Slash command endpoint: http://{host}:{port}/slack/commands")
    print(f"Events endpoint: http://{host}:{port}/slack/events")
    print(f"{'='*50}\n")

    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run_server()
