"""Slack integration for marketing content approval workflow.

Posts content suggestions to Slack with approval buttons.
When approved, triggers content publishing to website and LinkedIn.
"""

import json
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .content_generator import ContentSuggestion, BlogIdea, LinkedInPost

logger = logging.getLogger(__name__)


@dataclass
class ApprovalAction:
    """An approval action from Slack."""
    suggestion_id: str
    action: str  # "approve_all", "approve_blog", "approve_linkedin", "reject"
    user_id: str
    user_name: str
    channel_id: str
    message_ts: str
    response_url: str


class SlackMarketingClient:
    """Slack client for marketing content approval workflow."""

    def __init__(
        self,
        webhook_url: str,
        bot_token: Optional[str] = None,
        app_token: Optional[str] = None,
    ):
        """Initialize the Slack marketing client.

        Args:
            webhook_url: Slack incoming webhook URL
            bot_token: Slack bot token (xoxb-...) for interactive features
            app_token: Slack app-level token (xapp-...) for Socket Mode
        """
        self.webhook_url = webhook_url
        self.bot_token = bot_token
        self.app_token = app_token

    def post_content_suggestion(
        self, suggestion: ContentSuggestion, image_path: Optional[str] = None
    ) -> Optional[str]:
        """Post a content suggestion to Slack for approval.

        Args:
            suggestion: The content suggestion to post
            image_path: Optional path to the generated image

        Returns:
            Message timestamp (ts) for tracking, or None on failure
        """
        blocks = self._build_suggestion_blocks(suggestion)

        payload = {
            "text": f"New Content Suggestion: {suggestion.blog_idea.title}",
            "blocks": blocks,
        }

        # If we have a bot token, use chat.postMessage for richer interactions
        if self.bot_token:
            return self._post_with_bot(payload, image_path)

        # Fall back to webhook
        return self._post_with_webhook(payload)

    def _build_suggestion_blocks(self, suggestion: ContentSuggestion) -> list:
        """Build Slack Block Kit blocks for a content suggestion.

        Args:
            suggestion: Content suggestion to format

        Returns:
            List of Slack blocks
        """
        blog = suggestion.blog_idea
        linkedin = suggestion.linkedin_post

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Foliox AI Marketing Lead - New Content Suggestion",
                },
            },
            {"type": "divider"},
            # Blog Idea Section
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*BLOG IDEA*\n\n"
                        f"*Title:* {blog.title}\n\n"
                        f"*Hook:* {blog.hook}\n\n"
                        f"*AI Angle:* {blog.ai_angle}"
                    ),
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Outline:*\n"
                        + "\n".join(f"  {i+1}. {s}" for i, s in enumerate(blog.outline))
                    ),
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Target Audience:*\n{blog.target_audience}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*SEO Keywords:*\n{', '.join(blog.seo_keywords[:5])}",
                    },
                ],
            },
            {"type": "divider"},
            # LinkedIn Post Section (manual posting - copy/paste)
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*LINKEDIN POST* _(copy for manual posting)_\n\n"
                        f"{linkedin.text[:500]}{'...' if len(linkedin.text) > 500 else ''}"
                    ),
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Hashtags:* {' '.join(linkedin.hashtags)}",
                },
            },
            {"type": "divider"},
            # X.com (Twitter) Post Section
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*X.COM POST* _(copy for manual posting)_\n\n"
                        f"{getattr(suggestion, 'twitter_post', None) and suggestion.twitter_post.text or '_No X.com post generated_'}"
                    ),
                },
            },
            *([{
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": f"*Type:* {suggestion.twitter_post.post_type} | *Tags:* {' '.join(suggestion.twitter_post.hashtags)}",
                }],
            }] if getattr(suggestion, 'twitter_post', None) else []),
            {"type": "divider"},
            # Source articles
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            f"*Sources:* "
                            + " | ".join(
                                f"<{a.url}|{a.source}>"
                                for a in suggestion.source_articles[:3]
                            )
                        ),
                    }
                ],
            },
            # Image prompt info
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Image Prompt:* {suggestion.image_prompt[:200]}",
                    }
                ],
            },
            {"type": "divider"},
            # Category tag
            *([{
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": f"*Category:* `{getattr(suggestion, 'content_category', 'general')}`",
                }],
            }] if getattr(suggestion, 'content_category', '') else []),
            # Approval actions
            {
                "type": "actions",
                "block_id": f"approval_{suggestion.id}",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Publish Blog"},
                        "style": "primary",
                        "action_id": "approve_blog",
                        "value": suggestion.id,
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Reject"},
                        "style": "danger",
                        "action_id": "reject",
                        "value": suggestion.id,
                    },
                ],
            },
            # Instruction
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            "Reply with images to include them in the post. "
                            "Click a button to publish to blog. "
                            "Copy LinkedIn/X.com text above for manual posting."
                        ),
                    }
                ],
            },
        ]

        return blocks

    def post_approval_update(
        self,
        suggestion_id: str,
        action: str,
        user_name: str,
        response_url: str,
    ) -> None:
        """Post an approval status update to Slack.

        Args:
            suggestion_id: The suggestion that was acted upon
            action: The action taken
            user_name: Who took the action
            response_url: Slack response URL for updating the message
        """
        status_emoji = {
            "approve_all": "white_check_mark",
            "approve_blog": "memo",
            "approve_linkedin": "briefcase",
            "reject": "x",
        }

        status_text = {
            "approve_all": "APPROVED - Publishing blog + LinkedIn post",
            "approve_blog": "APPROVED - Publishing blog post only",
            "approve_linkedin": "APPROVED - Publishing LinkedIn post only",
            "reject": "REJECTED - Content will not be published",
        }

        emoji = status_emoji.get(action, "question")
        text = status_text.get(action, "Unknown action")

        payload = {
            "replace_original": False,
            "text": f":{emoji}: *{text}*\nBy @{user_name} | Suggestion: `{suggestion_id}`",
        }

        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            response_url,
            data=data,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                logger.info(f"Posted approval update for {suggestion_id}: {action}")
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            logger.error(f"Failed to post approval update: {e}")

    def post_publishing_status(
        self,
        suggestion_id: str,
        blog_url: Optional[str] = None,
        linkedin_url: Optional[str] = None,
    ) -> None:
        """Post publishing status back to Slack.

        Args:
            suggestion_id: The suggestion that was published
            blog_url: URL of the published blog post
            linkedin_url: URL of the published LinkedIn post
        """
        lines = [":rocket: *Content Published!*", f"Suggestion: `{suggestion_id}`", ""]

        if blog_url:
            lines.append(f":memo: *Blog:* <{blog_url}|View Post>")
        if linkedin_url:
            lines.append(f":briefcase: *LinkedIn:* <{linkedin_url}|View Post>")

        if not blog_url and not linkedin_url:
            lines.append(":warning: No URLs returned from publishing.")

        payload = {
            "text": "\n".join(lines),
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "\n".join(lines)},
                }
            ],
        }

        self._post_with_webhook(payload)

    def get_thread_images(
        self, channel_id: str, message_ts: str
    ) -> list[str]:
        """Get image URLs from replies to a Slack message thread.

        Args:
            channel_id: Channel ID
            message_ts: Parent message timestamp

        Returns:
            List of image file URLs from the thread
        """
        if not self.bot_token:
            logger.warning("Bot token required for reading thread replies")
            return []

        url = (
            f"https://slack.com/api/conversations.replies"
            f"?channel={channel_id}&ts={message_ts}"
        )

        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {self.bot_token}"},
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode("utf-8"))

            if not result.get("ok"):
                logger.error(f"Slack API error: {result.get('error')}")
                return []

            image_urls = []
            for message in result.get("messages", []):
                for file_info in message.get("files", []):
                    mimetype = file_info.get("mimetype", "")
                    if mimetype.startswith("image/"):
                        file_url = (
                            file_info.get("url_private_download")
                            or file_info.get("url_private")
                        )
                        if file_url:
                            image_urls.append(file_url)

            return image_urls

        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            logger.error(f"Failed to get thread replies: {e}")
            return []

    def _post_with_webhook(self, payload: dict) -> Optional[str]:
        """Post a message using the webhook URL.

        Args:
            payload: Message payload

        Returns:
            None (webhooks don't return message ts)
        """
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            self.webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                logger.info("Message posted via webhook")
                return None
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            logger.error(f"Webhook post failed: {e}")
            return None

    def _post_with_bot(
        self, payload: dict, image_path: Optional[str] = None
    ) -> Optional[str]:
        """Post a message using the bot token for richer interactions.

        Args:
            payload: Message payload
            image_path: Optional image to upload

        Returns:
            Message timestamp or None
        """
        if not self.bot_token:
            return self._post_with_webhook(payload)

        # If we have an image, upload it first
        if image_path:
            self._upload_image(image_path, payload.get("channel", ""))

        # Post the message
        post_payload = {**payload}
        if "channel" not in post_payload:
            # Fall back to webhook if no channel specified
            return self._post_with_webhook(payload)

        data = json.dumps(post_payload).encode("utf-8")

        req = urllib.request.Request(
            "https://slack.com/api/chat.postMessage",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.bot_token}",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode("utf-8"))

            if result.get("ok"):
                ts = result.get("ts")
                logger.info(f"Message posted via bot: {ts}")
                return ts
            else:
                logger.error(f"Bot post failed: {result.get('error')}")
                return self._post_with_webhook(payload)

        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            logger.error(f"Bot post failed: {e}")
            return self._post_with_webhook(payload)

    def _upload_image(self, image_path: str, channel: str) -> None:
        """Upload an image to a Slack channel.

        Args:
            image_path: Path to the image file
            channel: Channel ID to upload to
        """
        if not self.bot_token:
            return

        import mimetypes

        content_type = mimetypes.guess_type(image_path)[0] or "image/png"
        filename = image_path.split("/")[-1]

        # Read the file
        with open(image_path, "rb") as f:
            file_data = f.read()

        # Build multipart form data
        boundary = "----FormBoundary7MA4YWxkTrZu0gW"
        body_parts = []

        # Channel field
        body_parts.append(f"--{boundary}")
        body_parts.append('Content-Disposition: form-data; name="channels"')
        body_parts.append("")
        body_parts.append(channel)

        # Title field
        body_parts.append(f"--{boundary}")
        body_parts.append('Content-Disposition: form-data; name="title"')
        body_parts.append("")
        body_parts.append("AI Marketing Lead - Generated Image")

        body_str = "\r\n".join(body_parts) + "\r\n"
        body_bytes = body_str.encode("utf-8")

        # File field
        file_header = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        )
        file_footer = f"\r\n--{boundary}--\r\n"

        full_body = body_bytes + file_header.encode("utf-8") + file_data + file_footer.encode("utf-8")

        req = urllib.request.Request(
            "https://slack.com/api/files.upload",
            data=full_body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Authorization": f"Bearer {self.bot_token}",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                if result.get("ok"):
                    logger.info(f"Image uploaded to Slack: {filename}")
                else:
                    logger.error(f"Image upload failed: {result.get('error')}")
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            logger.error(f"Image upload failed: {e}")

    def parse_interaction_payload(self, payload_str: str) -> Optional[ApprovalAction]:
        """Parse a Slack interaction payload (from button clicks).

        Args:
            payload_str: URL-encoded payload string from Slack

        Returns:
            ApprovalAction or None
        """
        try:
            data = json.loads(payload_str)
        except json.JSONDecodeError:
            logger.error("Failed to parse interaction payload")
            return None

        if data.get("type") != "block_actions":
            return None

        actions = data.get("actions", [])
        if not actions:
            return None

        action = actions[0]
        user = data.get("user", {})
        channel = data.get("channel", {})
        message = data.get("message", {})

        return ApprovalAction(
            suggestion_id=action.get("value", ""),
            action=action.get("action_id", ""),
            user_id=user.get("id", ""),
            user_name=user.get("username", ""),
            channel_id=channel.get("id", ""),
            message_ts=message.get("ts", ""),
            response_url=data.get("response_url", ""),
        )
