"""Main agent orchestrator for Gmail-Slack cost monitoring."""

import logging
import time
from datetime import datetime
from typing import Optional

from .gmail_client import GmailClient
from .slack_client import SlackClient
from .cost_processor import CostProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CostMonitorAgent:
    """Agent that monitors Gmail for cost data and sends Slack notifications."""

    def __init__(
        self,
        gmail_credentials_path: str,
        slack_bot_token: str,
        slack_channel: str,
        subject_pattern: str = r'Cost Data|Cost Report|Daily Costs',
        watch_sender: Optional[str] = None,
        poll_interval: int = 60
    ):
        """Initialize the cost monitor agent.

        Args:
            gmail_credentials_path: Path to Google OAuth credentials JSON
            slack_bot_token: Slack bot OAuth token
            slack_channel: Slack channel ID for notifications
            subject_pattern: Regex pattern to match cost email subjects
            watch_sender: Optional sender email to filter by
            poll_interval: Seconds between email checks
        """
        logger.info("Initializing Cost Monitor Agent...")

        self.gmail = GmailClient(credentials_path=gmail_credentials_path)
        self.slack = SlackClient(bot_token=slack_bot_token, default_channel=slack_channel)
        self.cost_processor = CostProcessor()

        self.subject_pattern = subject_pattern
        self.watch_sender = watch_sender
        self.poll_interval = poll_interval

        # Track processed emails to avoid duplicates
        self._processed_emails: set[str] = set()

        logger.info("Agent initialized successfully")

    def process_email(self, email: dict) -> None:
        """Process a single cost data email.

        This method:
        1. Sends a Slack notification about the received email
        2. Parses cost data from the email
        3. Calculates trends
        4. Sends a reply to the customer with the trend report

        Args:
            email: Email dictionary from GmailClient
        """
        email_id = email['id']
        subject = email['subject']
        sender = email['sender']
        received_at = email['date']

        logger.info(f"Processing email: {subject} from {sender}")

        # Step 1: Send Slack notification
        try:
            self.slack.send_cost_alert(
                sender=sender,
                subject=subject,
                received_at=received_at
            )
            logger.info("Slack notification sent successfully")
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

        # Step 2: Parse cost data from email
        costs = self.cost_processor.parse_cost_email(email['body'])
        logger.info(f"Parsed costs: {costs}")

        # Step 3: Calculate trends
        trends = self.cost_processor.calculate_trends(costs)
        logger.info(f"Calculated trends: {trends}")

        # Step 4: Send trend summary to Slack
        try:
            self.slack.send_trend_summary(trends)
            logger.info("Trend summary sent to Slack")
        except Exception as e:
            logger.error(f"Failed to send trend summary: {e}")

        # Step 5: Generate and send reply email
        try:
            trend_report = self.cost_processor.generate_trend_report(trends)

            # Extract sender email address (handle "Name <email>" format)
            import re
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

        # Step 6: Mark email as read
        try:
            self.gmail.mark_as_read(email_id)
            logger.info("Email marked as read")
        except Exception as e:
            logger.error(f"Failed to mark email as read: {e}")

        # Track as processed
        self._processed_emails.add(email_id)

    def check_for_emails(self) -> list[dict]:
        """Check for new cost data emails.

        Returns:
            List of new unprocessed emails matching criteria
        """
        logger.debug("Checking for new emails...")

        emails = self.gmail.get_unread_emails(
            subject_pattern=self.subject_pattern,
            sender=self.watch_sender
        )

        # Filter out already processed emails
        new_emails = [e for e in emails if e['id'] not in self._processed_emails]

        if new_emails:
            logger.info(f"Found {len(new_emails)} new email(s)")

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
        logger.info(f"Starting agent... polling every {self.poll_interval} seconds")
        logger.info(f"Watching for emails with subject matching: {self.subject_pattern}")
        if self.watch_sender:
            logger.info(f"Filtering by sender: {self.watch_sender}")

        try:
            while True:
                try:
                    processed = self.run_once()
                    if processed:
                        logger.info(f"Processed {processed} email(s)")
                except Exception as e:
                    logger.error(f"Error in polling cycle: {e}")

                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            logger.info("Agent stopped by user")
