"""Main agent orchestrator for Gmail-Slack OPIS fuel price monitoring.

Architecture:
    Email → Raw Capture (immutable) → Row Extraction → Derived Views → Response

All OPIS data is:
1. Captured losslessly (raw email preserved)
2. Extracted row-by-row with preserved semantics
3. Available for ML, audits, and reprocessing
"""

import logging
import re
import time
from datetime import datetime
from typing import Optional

from .gmail_client import GmailClient
from .slack_client import SlackWebhookClient
from .opis_parser import OPISParser
from .storage import OPISDataStore, DerivedViews
from .cost_processor import FuelPriceProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OPISMonitorAgent:
    """Agent that monitors Gmail for OPIS fuel pricing data and sends Slack notifications.

    Data flow:
    1. Receive email
    2. Store raw capture (lossless, immutable)
    3. Extract all rows (preserving semantics)
    4. Generate derived views for analysis
    5. Notify via Slack
    6. Reply with ingestion summary + trends
    """

    def __init__(
        self,
        gmail_credentials_path: str,
        slack_webhook_url: str,
        subject_pattern: str = r'OPIS Wholesale|OPIS Spot',
        watch_sender: Optional[str] = 'opisadmin@opisnet.com',
        poll_interval: int = 60,
        history_file: str = 'price_history.json',
        data_path: str = 'data'
    ):
        """Initialize the OPIS monitor agent.

        Args:
            gmail_credentials_path: Path to Google OAuth credentials JSON
            slack_webhook_url: Slack incoming webhook URL
            subject_pattern: Regex pattern to match OPIS email subjects
            watch_sender: Sender email to filter by (default: opisadmin@opisnet.com)
            poll_interval: Seconds between email checks
            history_file: Path to JSON file for legacy price history
            data_path: Base path for data lake storage
        """
        logger.info("Initializing OPIS Fuel Price Monitor Agent...")

        self.gmail = GmailClient(credentials_path=gmail_credentials_path)
        self.slack = SlackWebhookClient(webhook_url=slack_webhook_url)

        # New data lake architecture
        self.parser = OPISParser()
        self.data_store = OPISDataStore(base_path=data_path)
        self.derived_views = DerivedViews(self.data_store)

        # Legacy processor for trend analysis (will migrate to derived views)
        self.price_processor = FuelPriceProcessor(history_file=history_file)

        self.subject_pattern = subject_pattern
        self.watch_sender = watch_sender
        self.poll_interval = poll_interval

        # Track processed emails to avoid duplicates
        self._processed_emails: set[str] = set()

        logger.info("Agent initialized successfully")
        logger.info(f"Data storage path: {data_path}")

    def process_email(self, email: dict) -> None:
        """Process an OPIS pricing email with full data capture.

        Pipeline:
        1. Store raw capture (lossless, immutable)
        2. Extract all rows with preserved semantics
        3. Parse for legacy trend analysis
        4. Notify Slack
        5. Reply with explicit ingestion summary

        Args:
            email: Email dictionary from GmailClient
        """
        email_id = email['id']
        subject = email['subject']
        sender = email['sender']
        received_at = email['date']
        raw_body = email['body']

        logger.info(f"Processing OPIS email: {subject} from {sender}")

        # ================================================================
        # STEP 1: RAW CAPTURE (Lossless, Immutable)
        # ================================================================
        try:
            # Check for duplicates
            if self.data_store.capture_exists(raw_body):
                logger.warning("Duplicate email detected, skipping...")
                self._processed_emails.add(email_id)
                return

            # Parse to extract metadata
            opis_data = self.parser.parse(raw_body)

            # Store raw capture
            capture = self.data_store.store_raw_capture(
                raw_text=raw_body,
                sender=sender,
                subject=subject,
                received_at=received_at,
                account_number=opis_data.account_number,
                locations=opis_data.locations,
                market="Group 3"
            )
            capture_id = capture.id
            logger.info(f"Raw capture stored: {capture_id}")

        except Exception as e:
            logger.error(f"Failed to store raw capture: {e}")
            return

        # ================================================================
        # STEP 2: ROW-LEVEL EXTRACTION (Preserves Semantics)
        # ================================================================
        try:
            extracted_rows, retail_rows = self.parser.extract_rows(raw_body, capture_id)
            self.data_store.store_extracted_rows(capture_id, extracted_rows, retail_rows)

            total_rows = len(extracted_rows) + len(retail_rows)
            logger.info(f"Extracted {len(extracted_rows)} price rows, {len(retail_rows)} retail rows")

        except Exception as e:
            logger.error(f"Failed to extract rows: {e}")
            extracted_rows = []
            retail_rows = []
            total_rows = 0

        # ================================================================
        # STEP 3: LEGACY TREND ANALYSIS
        # ================================================================
        try:
            trends = self.price_processor.calculate_trends(opis_data)
            self.price_processor.update_history(opis_data)
            logger.info("Price trends calculated")
        except Exception as e:
            logger.error(f"Failed to calculate trends: {e}")
            trends = {'report_date': opis_data.report_date, 'locations': {}}

        # ================================================================
        # STEP 4: SLACK NOTIFICATIONS
        # ================================================================
        try:
            # Initial alert
            self.slack.send_opis_alert(
                sender=sender,
                subject=subject,
                received_at=received_at,
                report_date=opis_data.report_date or "Unknown",
                locations=opis_data.locations
            )

            # Trend summary
            slack_summary = self.price_processor.generate_slack_summary(trends)
            self.slack.send_fuel_price_summary(slack_summary)
            logger.info("Slack notifications sent")

        except Exception as e:
            logger.error(f"Failed to send Slack notifications: {e}")

        # ================================================================
        # STEP 5: CUSTOMER REPLY WITH INGESTION SUMMARY
        # ================================================================
        try:
            # Generate explicit ingestion summary + trend report
            reply_body = self._generate_customer_reply(
                opis_data=opis_data,
                trends=trends,
                capture_id=capture_id,
                total_rows=total_rows,
                extracted_rows=extracted_rows
            )

            # Extract sender email address
            email_match = re.search(r'<(.+?)>', sender)
            reply_to = email_match.group(1) if email_match else sender

            self.gmail.send_reply(
                thread_id=email['thread_id'],
                to=reply_to,
                subject=subject,
                body=reply_body
            )
            logger.info(f"Reply sent to {reply_to}")

        except Exception as e:
            logger.error(f"Failed to send reply: {e}")

        # ================================================================
        # STEP 6: MARK AS PROCESSED
        # ================================================================
        try:
            self.gmail.mark_as_read(email_id)
            logger.info("Email marked as read")
        except Exception as e:
            logger.error(f"Failed to mark email as read: {e}")

        self._processed_emails.add(email_id)

    def _generate_customer_reply(
        self,
        opis_data,
        trends: dict,
        capture_id: str,
        total_rows: int,
        extracted_rows: list
    ) -> str:
        """Generate customer reply with explicit ingestion summary.

        Sets trust + clarity by being explicit about what was captured.
        """
        report_date = opis_data.report_date or datetime.now().strftime('%Y-%m-%d')
        locations = ', '.join(opis_data.locations) if opis_data.locations else 'Unknown'

        # Count products
        products = set()
        for row in extracted_rows:
            if hasattr(row, 'product_group'):
                products.add(row.product_group)

        # Count vendors
        vendors = set()
        for row in extracted_rows:
            if hasattr(row, 'vendor') and row.vendor:
                vendors.add(row.vendor)

        lines = [
            "=" * 60,
            "MARKET PRICING FULLY INGESTED",
            "=" * 60,
            "",
            f"Source: OPIS (Oil Price Information Service)",
            f"Report Date: {report_date}",
            f"Account: #{opis_data.account_number or 'N/A'}",
            f"Capture ID: {capture_id}",
            "",
            "INGESTION SUMMARY",
            "-" * 40,
            f"  Records captured: {total_rows} price rows",
            f"  Markets: {locations}",
            f"  Product sections: {len(products)}",
            f"  Vendors: {', '.join(sorted(vendors)) if vendors else 'N/A'}",
            "",
            "All market data has been stored for:",
            "  - Historical analysis",
            "  - Pricing models",
            "  - Benchmark comparisons",
            "  - Audit trails",
            "",
            "LICENSE NOTICE: This data is for internal use only.",
            "Source attribution: Oil Price Information Service (OPIS)",
            "",
            "=" * 60,
            "",
        ]

        # Add trend report
        trend_report = self.price_processor.generate_trend_report(trends)
        lines.append(trend_report)

        lines.extend([
            "",
            "-" * 60,
            "No pricing has been applied to contracts or dispatch by default.",
            "Contact your administrator for pricing model configuration.",
        ])

        return '\n'.join(lines)

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

        # Show storage stats
        stats = self.data_store.get_statistics()
        logger.info(f"Data store: {stats['total_captures']} captures, {stats['total_rows_extracted']} rows")

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

    def get_storage_stats(self) -> dict:
        """Get current data storage statistics."""
        return self.data_store.get_statistics()


# Backwards compatibility alias
CostMonitorAgent = OPISMonitorAgent
