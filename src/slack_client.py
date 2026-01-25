"""Slack client for sending notifications."""

from typing import Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackClient:
    """Client for sending Slack notifications."""

    def __init__(self, bot_token: str, default_channel: Optional[str] = None):
        """Initialize Slack client.

        Args:
            bot_token: Slack bot OAuth token (xoxb-...)
            default_channel: Default channel ID for notifications
        """
        self.client = WebClient(token=bot_token)
        self.default_channel = default_channel

    def send_notification(self, message: str, channel: Optional[str] = None,
                          blocks: Optional[list] = None) -> dict:
        """Send a notification message to Slack.

        Args:
            message: Text message to send (used as fallback for blocks)
            channel: Channel ID to send to (uses default if not specified)
            blocks: Optional Slack Block Kit blocks for rich formatting

        Returns:
            Slack API response

        Raises:
            SlackApiError: If the message fails to send
        """
        target_channel = channel or self.default_channel
        if not target_channel:
            raise ValueError("No channel specified and no default channel set")

        try:
            response = self.client.chat_postMessage(
                channel=target_channel,
                text=message,
                blocks=blocks
            )
            return response.data
        except SlackApiError as e:
            print(f"Slack API error: {e.response['error']}")
            raise

    def send_cost_alert(self, sender: str, subject: str, received_at: str,
                        channel: Optional[str] = None) -> dict:
        """Send a formatted cost data received alert.

        Args:
            sender: Email sender address
            subject: Email subject
            received_at: When the email was received
            channel: Optional channel override

        Returns:
            Slack API response
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Cost Data Received",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*From:*\n{sender}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Received:*\n{received_at}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Subject:*\n{subject}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "The agent is processing cost trends and will reply to the sender."
                    }
                ]
            }
        ]

        message = f"Cost data received from {sender}: {subject}"
        return self.send_notification(message, channel, blocks)

    def send_trend_summary(self, trends: dict, channel: Optional[str] = None) -> dict:
        """Send a summary of cost trends to Slack.

        Args:
            trends: Dictionary containing trend data
            channel: Optional channel override

        Returns:
            Slack API response
        """
        trend_text = []
        for category, data in trends.items():
            direction = "up" if data.get('change', 0) > 0 else "down"
            emoji = ":chart_with_upwards_trend:" if direction == "up" else ":chart_with_downwards_trend:"
            trend_text.append(
                f"{emoji} *{category}*: ${data.get('current', 0):,.2f} "
                f"({data.get('change', 0):+.1f}%)"
            )

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Daily Cost Trends Summary",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "\n".join(trend_text) if trend_text else "No trend data available"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Total: ${trends.get('total', {}).get('current', 0):,.2f}"
                    }
                ]
            }
        ]

        message = "Daily cost trends summary"
        return self.send_notification(message, channel, blocks)
