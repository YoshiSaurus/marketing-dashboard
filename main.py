#!/usr/bin/env python3
"""Main entry point for the OPIS Fuel Price Monitor Agent."""

import os
import sys

from dotenv import load_dotenv

from src.agent import OPISMonitorAgent


def main():
    """Initialize and run the OPIS fuel price monitor agent."""
    # Load environment variables
    load_dotenv()

    # Get configuration from environment
    gmail_credentials = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
    slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    subject_pattern = os.getenv('COST_EMAIL_SUBJECT_PATTERN', r'OPIS Wholesale|OPIS Spot')
    watch_sender = os.getenv('WATCH_SENDER_EMAIL') or None
    poll_interval = int(os.getenv('POLL_INTERVAL', '60'))
    history_file = os.getenv('PRICE_HISTORY_FILE', 'price_history.json')
    data_path = os.getenv('DATA_PATH', 'data')
    reply_to_email = os.getenv('REPLY_TO_EMAIL', 'bsims@pakasak.net')
    cc_email = os.getenv('CC_EMAIL', 'ayush@foliox.ai')

    # Validate required configuration
    if not slack_webhook_url:
        print("Error: SLACK_WEBHOOK_URL is required. Set it in .env file or environment.")
        print("Example: https://hooks.slack.com/services/T.../B.../...")
        sys.exit(1)

    if not os.path.exists(gmail_credentials):
        print(f"Warning: Gmail credentials file not found at '{gmail_credentials}'")
        print("You'll need to download it from Google Cloud Console.")
        print("See README.md for setup instructions.")

    # Create and run agent
    agent = OPISMonitorAgent(
        gmail_credentials_path=gmail_credentials,
        slack_webhook_url=slack_webhook_url,
        subject_pattern=subject_pattern,
        watch_sender=watch_sender,
        poll_interval=poll_interval,
        history_file=history_file,
        data_path=data_path,
        reply_to_email=reply_to_email,
        cc_email=cc_email
    )

    print("=" * 60)
    print("FOLIOX PRICING AGENT")
    print("=" * 60)
    print(f"  Polling interval: {poll_interval} seconds")
    print(f"  Subject pattern: {subject_pattern}")
    print(f"  Watch sender: {watch_sender or 'All senders'}")
    print(f"  Reply to: {reply_to_email}")
    print(f"  CC: {cc_email}")
    print(f"  Data storage: {data_path}/")
    print("=" * 60)
    print("Agent is running. Press Ctrl+C to stop.")
    print()

    agent.run()


if __name__ == '__main__':
    main()
