"""Main agent orchestrator for Gmail-Slack OPIS fuel price monitoring."""

import logging
import re
import time
from datetime import datetime
from typing import Optional

from .gmail_client import GmailClient
from .slack_client import SlackClient
from .cost_processor import FuelPriceProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OPISMonitorAgent:
    """Agent that monitors Gmail for OPIS fuel pricing data and sends Slack notifications."""

    def __init__(
        self,
        gmail_credentials_path: str,
        slack_bot_token: str,
        slack_channel: str,
        subject_pattern: str = r'OPIS Wholesale|OPIS Spot',
        watch_sender: Optional[str] = 'opisadmin@opisnet.com',
        poll_interval: int = 60,
        history_file: str = 'price_history.json'
    ):
        """Initialize the OPIS monitor agent.

        Args:
            gmail_credentials_path: Path to Google OAuth credentials JSON
            slack_bot_token: Slack bot OAuth token
            slack_channel: Slack channel ID for notifications
            subject_pattern: Regex pattern to match OPIS email subjects
            watch_sender: Sender email to filter by (default: opisadmin@opisnet.com)
            poll_interval: Seconds between email checks
            history_file: Path to JSON file for storing price history
        """
        logger.info("Initializing OPIS Fuel Price Monitor Agent...")

        self.gmail = GmailClient(credentials_path=gmail_credentials_path)
        self.slack = SlackClient(bot_token=slack_bot_token, default_channel=slack_channel)
        self.price_processor = FuelPriceProcessor(history_file=history_file)

        self.subject_pattern = subject_pattern
        self.watch_sender = watch_sender
        self.poll_interval = poll_interval

        # Track processed emails to avoid duplicates
        self._processed_emails: set[str] = set()

        logger.info("Agent initialized successfully")

    def process_email(self, email: dict) -> None:
        """Process an OPIS pricing email.

        This method:
        1. Parses OPIS data from the email
        2. Sends a Slack notification about the received email
        3. Calculates price trends
        4. Updates price history
        5. Sends trend summary to Slack
        6. Sends a reply to the customer with the trend report

        Args:
            email: Email dictionary from GmailClient
        """
        email_id = email['id']
        subject = email['subject']
        sender = email['sender']
        received_at = email['date']

        logger.info(f"Processing OPIS email: {subject} from {sender}")

        # Step 1: Parse OPIS data from email
        try:
            opis_data = self.price_processor.parse_opis_email(email['body'])
            logger.info(f"Parsed OPIS data for {len(opis_data.locations)} location(s): {opis_data.locations}")
            logger.info(f"Report date: {opis_data.report_date}")
            logger.info(f"Found {len(opis_data.products)} product sections")
        except Exception as e:
            logger.error(f"Failed to parse OPIS data: {e}")
            return

        # Step 2: Send Slack notification about receipt
        try:
            self.slack.send_opis_alert(
                sender=sender,
                subject=subject,
                received_at=received_at,
                report_date=opis_data.report_date or "Unknown",
                locations=opis_data.locations
            )
            logger.info("Slack notification sent successfully")
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

        # Step 3: Calculate trends
        try:
            trends = self.price_processor.calculate_trends(opis_data)
            logger.info("Price trends calculated")
        except Exception as e:
            logger.error(f"Failed to calculate trends: {e}")
            trends = {'report_date': opis_data.report_date, 'locations': {}}

        # Step 4: Update price history for future trend analysis
        try:
            self.price_processor.update_history(opis_data)
            logger.info("Price history updated")
        except Exception as e:
            logger.error(f"Failed to update price history: {e}")

        # Step 5: Send trend summary to Slack
        try:
            slack_summary = self.price_processor.generate_slack_summary(trends)
            self.slack.send_fuel_price_summary(slack_summary)
            logger.info("Fuel price summary sent to Slack")
        except Exception as e:
            logger.error(f"Failed to send trend summary: {e}")

        # Step 6: Generate and send reply email
        try:
            trend_report = self.price_processor.generate_trend_report(trends)

            # Extract sender email address (handle "Name <email>" format)
            email_match = re.search(r'<(.+?)>', sender)
            reply_to = email_match.group(1) if email_match else sender

            self.gmail.send_reply(
                thread_id=email['thread_id'],
                to=reply_to,
                subject=subject,
                body=trend_report
            )
            logger.info(f"Reply sent to {reply_to}")
        except Exception as e:
            logger.error(f"Failed to send reply: {e}")

        # Step 7: Mark email as read
        try:
            self.gmail.mark_as_read(email_id)
            logger.info("Email marked as read")
        except Exception as e:
            logger.error(f"Failed to mark email as read: {e}")

        # Track as processed
        self._processed_emails.add(email_id)

    def check_for_emails(self) -> list[dict]:
        """Check for new OPIS pricing emails.

        Returns:
            List of new unprocessed emails matching criteria
        """
        logger.debug("Checking for new OPIS emails...")

        emails = self.gmail.get_unread_emails(
            subject_pattern=self.subject_pattern,
            sender=self.watch_sender
        )

        # Filter out already processed emails
        new_emails = [e for e in emails if e['id'] not in self._processed_emails]

        if new_emails:
            logger.info(f"Found {len(new_emails)} new OPIS email(s)")

        return new_emails

    def run_once(self) -> int:
        """Run a single check cycle.

        Returns:
            Number of emails processed
        """
        emails = self.check_for_emails()

        for email in emails:
            try:
                self.process_email(email)
            except Exception as e:
                logger.error(f"Error processing email {email['id']}: {e}")

        return len(emails)

    def run(self) -> None:
        """Run the agent continuously, polling for new emails.

        This method runs indefinitely, checking for new emails
        at the configured poll interval.
        """
        logger.info(f"Starting OPIS Monitor Agent... polling every {self.poll_interval} seconds")
        logger.info(f"Watching for emails with subject matching: {self.subject_pattern}")
        if self.watch_sender:
            logger.info(f"Filtering by sender: {self.watch_sender}")

        try:
            while True:
                try:
                    processed = self.run_once()
                    if processed:
                        logger.info(f"Processed {processed} OPIS email(s)")
                except Exception as e:
                    logger.error(f"Error in polling cycle: {e}")

                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            logger.info("Agent stopped by user")


# Backwards compatibility alias
CostMonitorAgent = OPISMonitorAgent
