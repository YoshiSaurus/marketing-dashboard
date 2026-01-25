#!/usr/bin/env python3
"""Main entry point for the Gmail-Slack Cost Monitor Agent."""

import os
import sys

from dotenv import load_dotenv

from src.agent import CostMonitorAgent


def main():
    """Initialize and run the cost monitor agent."""
    # Load environment variables
    load_dotenv()

    # Get configuration from environment
    gmail_credentials = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
    slack_token = os.getenv('SLACK_BOT_TOKEN')
    slack_channel = os.getenv('SLACK_CHANNEL_ID')
    subject_pattern = os.getenv('COST_EMAIL_SUBJECT_PATTERN', r'Cost Data|Cost Report|Daily Costs')
    watch_sender = os.getenv('WATCH_SENDER_EMAIL') or None
    poll_interval = int(os.getenv('POLL_INTERVAL', '60'))

    # Validate required configuration
    if not slack_token:
        print("Error: SLACK_BOT_TOKEN is required. Set it in .env file or environment.")
        sys.exit(1)

    if not slack_channel:
        print("Error: SLACK_CHANNEL_ID is required. Set it in .env file or environment.")
        sys.exit(1)

    if not os.path.exists(gmail_credentials):
        print(f"Warning: Gmail credentials file not found at '{gmail_credentials}'")
        print("You'll need to download it from Google Cloud Console.")
        print("See README.md for setup instructions.")

    # Create and run agent
    agent = CostMonitorAgent(
        gmail_credentials_path=gmail_credentials,
        slack_bot_token=slack_token,
        slack_channel=slack_channel,
        subject_pattern=subject_pattern,
        watch_sender=watch_sender,
        poll_interval=poll_interval
    )

    print("=" * 50)
    print("Gmail-Slack Cost Monitor Agent")
    print("=" * 50)
    print(f"  Polling interval: {poll_interval} seconds")
    print(f"  Subject pattern: {subject_pattern}")
    print(f"  Watch sender: {watch_sender or 'All senders'}")
    print("=" * 50)
    print("Agent is running. Press Ctrl+C to stop.")
    print()

    agent.run()


if __name__ == '__main__':
    main()
