"""Flask server for handling Slack interactions (button clicks, events).

This server handles:
- Interactive button clicks for content approval/rejection
- URL verification for Slack Events API
- File shared events (for thread reply images)
"""

import json
import logging
import os
import threading
from typing import Optional

logger = logging.getLogger(__name__)


def create_marketing_app(agent):
    """Create Flask app for marketing agent Slack interactions.

    Args:
        agent: MarketingAgent instance

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
        return jsonify({
            "status": "healthy",
            "agent": "foliox-ai-marketing-lead",
            "pending_suggestions": len(agent._pending),
            "published": len(agent._published),
        })

    @app.route("/slack/interactions", methods=["POST"])
    def handle_interaction():
        """Handle Slack interactive component payloads (button clicks)."""
        payload_str = request.form.get("payload", "")
        if not payload_str:
            return jsonify({"error": "No payload"}), 400

        approval = agent.slack.parse_interaction_payload(payload_str)
        if not approval:
            return jsonify({"error": "Invalid payload"}), 400

        logger.info(
            f"Received approval action: {approval.action} "
            f"for {approval.suggestion_id} by {approval.user_name}"
        )

        # Process approval in background so we respond to Slack quickly
        thread = threading.Thread(
            target=agent.handle_approval,
            args=(approval,),
        )
        thread.start()

        # Immediate acknowledgment to Slack
        action_text = {
            "approve_all": "Approved! Publishing blog + LinkedIn post...",
            "approve_blog": "Approved! Publishing blog post...",
            "approve_linkedin": "Approved! Publishing LinkedIn post...",
            "reject": "Rejected. Content will not be published.",
        }

        return jsonify({
            "text": action_text.get(approval.action, "Processing..."),
        })

    @app.route("/slack/events", methods=["POST"])
    def handle_event():
        """Handle Slack Events API."""
        data = request.get_json(silent=True) or {}

        # URL verification challenge
        if data.get("type") == "url_verification":
            return jsonify({"challenge": data.get("challenge")})

        # Handle events
        event = data.get("event", {})
        event_type = event.get("type")

        if event_type == "message" and event.get("subtype") == "file_share":
            # Someone shared a file in a thread - might be an image for content
            thread_ts = event.get("thread_ts")
            if thread_ts:
                logger.info(f"File shared in thread {thread_ts}")
                # The approval handler will pick up thread images when publishing

        return jsonify({"ok": True})

    @app.route("/scan", methods=["POST"])
    def trigger_scan():
        """Manually trigger a news scan cycle."""
        thread = threading.Thread(target=agent.run_scan_cycle)
        thread.start()
        return jsonify({
            "status": "scan_started",
            "message": "News scan cycle triggered. Results will be posted to Slack.",
        })

    return app


def run_marketing_server(host: str = "0.0.0.0", port: int = 3001):
    """Run the marketing agent server.

    Args:
        host: Host to bind to
        port: Port to listen on
    """
    from dotenv import load_dotenv
    load_dotenv()

    from .marketing_agent import MarketingAgent

    # Load configuration from environment
    agent = MarketingAgent(
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        gemini_api_key=os.environ.get("GEMINI_API_KEY"),
        banana_api_key=os.environ.get("BANANA_API_KEY"),
        google_search_api_key=os.environ.get("GOOGLE_SEARCH_API_KEY"),
        google_search_cx=os.environ.get("GOOGLE_SEARCH_CX"),
        slack_webhook_url=os.environ.get(
            "MARKETING_SLACK_WEBHOOK_URL",
            os.environ.get("SLACK_WEBHOOK_URL", ""),
        ),
        slack_bot_token=os.environ.get("SLACK_BOT_TOKEN"),
        slack_app_token=os.environ.get("SLACK_APP_TOKEN"),
        website_api_url=os.environ.get("WEBSITE_API_URL"),
        website_api_key=os.environ.get("WEBSITE_API_KEY"),
        linkedin_access_token=os.environ.get("LINKEDIN_ACCESS_TOKEN"),
        linkedin_org_id=os.environ.get("LINKEDIN_ORG_ID"),
        scan_interval=int(os.environ.get("MARKETING_SCAN_INTERVAL", "3600")),
        num_suggestions=int(os.environ.get("MARKETING_NUM_SUGGESTIONS", "3")),
        output_dir=os.environ.get("MARKETING_OUTPUT_DIR", "marketing_output"),
    )

    app = create_marketing_app(agent)

    # Start the scan loop in a background thread
    scan_thread = threading.Thread(target=agent.run, daemon=True)
    scan_thread.start()

    print(f"\n{'='*60}")
    print("FOLIOX AI MARKETING LEAD - Server")
    print(f"{'='*60}")
    print(f"Server running on http://{host}:{port}")
    print(f"Health check:      http://{host}:{port}/health")
    print(f"Slack interactions: http://{host}:{port}/slack/interactions")
    print(f"Slack events:      http://{host}:{port}/slack/events")
    print(f"Manual scan:       POST http://{host}:{port}/scan")
    print(f"{'='*60}\n")

    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run_marketing_server()
