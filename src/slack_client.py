"""Slack client for sending fuel pricing notifications via webhook."""

import json
import urllib.request
import urllib.error
from typing import Optional


class SlackWebhookClient:
    """Client for sending Slack notifications via incoming webhook.

    Webhooks are simpler than bot tokens - just POST to a URL.
    No OAuth, no channel IDs, no scopes needed.
    """

    def __init__(self, webhook_url: str):
        """Initialize Slack webhook client.

        Args:
            webhook_url: Slack incoming webhook URL
                        (e.g., https://hooks.slack.com/services/T.../B.../...)
        """
        self.webhook_url = webhook_url

    def send_notification(self, message: str, blocks: Optional[list] = None) -> dict:
        """Send a notification message to Slack via webhook.

        Args:
            message: Text message to send (used as fallback for blocks)
            blocks: Optional Slack Block Kit blocks for rich formatting

        Returns:
            Response dict with status

        Raises:
            Exception: If the webhook request fails
        """
        payload = {"text": message}

        if blocks:
            payload["blocks"] = blocks

        data = json.dumps(payload).encode('utf-8')

        req = urllib.request.Request(
            self.webhook_url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        try:
            with urllib.request.urlopen(req) as response:
                return {"ok": True, "status": response.status}
        except urllib.error.HTTPError as e:
            print(f"Slack webhook error: {e.code} - {e.reason}")
            raise
        except urllib.error.URLError as e:
            print(f"Slack webhook connection error: {e.reason}")
            raise

    def send_opis_alert(self, sender: str, subject: str, received_at: str,
                        report_date: str, locations: list[str]) -> dict:
        """Send an alert when OPIS pricing data is received.

        Args:
            sender: Email sender address
            subject: Email subject
            received_at: When the email was received
            report_date: Date of the OPIS report
            locations: List of locations in the report

        Returns:
            Response dict
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
        return self.send_notification(message, blocks)

    def send_fuel_price_summary(self, summary: dict) -> dict:
        """Send a summary of fuel price trends to Slack.

        Args:
            summary: Dictionary from FuelPriceProcessor.generate_slack_summary()

        Returns:
            Response dict
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
        return self.send_notification(message, blocks)

    def send_ingestion_summary(self, capture_id: str, report_date: str,
                                locations: list[str], total_rows: int,
                                vendors: list[str]) -> dict:
        """Send an ingestion summary to Slack.

        Args:
            capture_id: Unique capture ID
            report_date: Date of the OPIS report
            locations: List of locations
            total_rows: Total number of rows captured
            vendors: List of vendor names

        Returns:
            Response dict
        """
        locations_text = ", ".join(locations) if locations else "Unknown"
        vendors_text = ", ".join(sorted(vendors)) if vendors else "N/A"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Market Pricing Fully Ingested",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Source:*\nOPIS"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Report Date:*\n{report_date}"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Records Captured:*\n{total_rows} price rows"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Capture ID:*\n`{capture_id}`"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Markets:* {locations_text}\n*Vendors:* {vendors_text}"
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
                        "text": ":white_check_mark: All data stored for historical analysis, pricing models, and audit trails"
                    }
                ]
            }
        ]

        message = f"OPIS pricing data ingested: {total_rows} rows from {locations_text}"
        return self.send_notification(message, blocks)


# Backwards compatibility - alias for old code
SlackClient = SlackWebhookClient
