"""Slack client for sending fuel pricing notifications."""

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

    def send_opis_alert(self, sender: str, subject: str, received_at: str,
                        report_date: str, locations: list[str],
                        channel: Optional[str] = None) -> dict:
        """Send an alert when OPIS pricing data is received.

        Args:
            sender: Email sender address
            subject: Email subject
            received_at: When the email was received
            report_date: Date of the OPIS report
            locations: List of locations in the report
            channel: Optional channel override

        Returns:
            Slack API response
        """
        locations_text = ", ".join(locations) if locations else "Unknown"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "OPIS Fuel Pricing Data Received",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Report Date:*\n{report_date}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Received:*\n{received_at}"
                    }
                ]
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
                        "text": f"*Locations:*\n{locations_text}"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": ":fuel_pump: Processing fuel price trends and preparing response..."
                    }
                ]
            }
        ]

        message = f"OPIS fuel pricing data received for {report_date} - {locations_text}"
        return self.send_notification(message, channel, blocks)

    def send_fuel_price_summary(self, summary: dict, channel: Optional[str] = None) -> dict:
        """Send a summary of fuel price trends to Slack.

        Args:
            summary: Dictionary from FuelPriceProcessor.generate_slack_summary()
            channel: Optional channel override

        Returns:
            Slack API response
        """
        report_date = summary.get('report_date', 'Unknown')

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Fuel Price Trends - {report_date}",
                    "emoji": True
                }
            }
        ]

        # Add location sections
        for location in summary.get('locations', []):
            location_name = location.get('name', 'Unknown')

            # Build price table
            price_lines = []
            for product in location.get('products', []):
                name = product.get('name', '')
                # Shorten product names for display
                short_name = name.replace('Conventional Clear ', '').replace('Ultra Low Sulfur ', 'ULS ')
                rack_avg = product.get('rack_avg')
                change = product.get('change')
                direction = product.get('direction', 'new')

                # Direction indicators
                if direction == 'up':
                    indicator = ":arrow_up:"
                elif direction == 'down':
                    indicator = ":arrow_down:"
                elif direction == 'stable':
                    indicator = ":left_right_arrow:"
                else:
                    indicator = ":new:"

                if rack_avg:
                    change_str = f"{change:+.2f}" if change is not None else "N/A"
                    price_lines.append(f"{indicator} *{short_name}*: {rack_avg:.2f} cpg ({change_str})")

            if price_lines:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{location_name}*\n" + "\n".join(price_lines)
                    }
                })

        # Add highlights/insights
        highlights = summary.get('highlights', [])
        if highlights:
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Market Insights:*\n" + "\n".join(f"• {h}" for h in highlights)
                }
            })

        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": ":email: Customer reply sent with detailed trend report"
                }
            ]
        })

        message = f"Fuel price trends for {report_date}"
        return self.send_notification(message, channel, blocks)

    # Keep backward compatibility
    def send_cost_alert(self, sender: str, subject: str, received_at: str,
                        channel: Optional[str] = None) -> dict:
        """Send a formatted cost data received alert (legacy method).

        Args:
            sender: Email sender address
            subject: Email subject
            received_at: When the email was received
            channel: Optional channel override

        Returns:
            Slack API response
        """
        return self.send_opis_alert(
            sender=sender,
            subject=subject,
            received_at=received_at,
            report_date="See email",
            locations=[],
            channel=channel
        )

    def send_trend_summary(self, trends: dict, channel: Optional[str] = None) -> dict:
        """Send a summary of trends to Slack (legacy method).

        Args:
            trends: Dictionary containing trend data
            channel: Optional channel override

        Returns:
            Slack API response
        """
        # Convert old format to new format if needed
        if 'locations' in trends:
            return self.send_fuel_price_summary(trends, channel)

        # Handle legacy format
        trend_text = []
        for category, data in trends.items():
            if isinstance(data, dict) and 'current' in data:
                direction = "up" if data.get('change', 0) > 0 else "down"
                emoji = ":chart_with_upwards_trend:" if direction == "up" else ":chart_with_downwards_trend:"
                trend_text.append(
                    f"{emoji} *{category}*: {data.get('current', 0):.2f} cpg "
                    f"({data.get('change', 0):+.1f}%)"
                )

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Daily Price Trends Summary",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "\n".join(trend_text) if trend_text else "No trend data available"
                }
            }
        ]

        message = "Daily price trends summary"
        return self.send_notification(message, channel, blocks)
