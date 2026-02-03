#!/usr/bin/env python3
"""
Foliox Document Scanner Bot - Main Entry Point

A Slack bot that scans Bill of Lading (BOL) documents and extracts key fields
using Claude Vision AI.

Usage:
    python scan_server.py [--host HOST] [--port PORT]

Environment Variables:
    SLACK_BOT_TOKEN      - Slack Bot User OAuth Token (xoxb-...)
    SLACK_SIGNING_SECRET - Slack App signing secret
    ANTHROPIC_API_KEY    - Anthropic API key for Claude Vision
    SLACK_WEBHOOK_URL    - (Optional) Webhook URL for notifications

Slack App Setup:
    1. Create a Slack App at https://api.slack.com/apps
    2. Add Bot Token Scopes: chat:write, files:read
    3. Create a Slash Command: /scan
    4. Enable Event Subscriptions for: file_shared
    5. Install the app to your workspace
"""

import argparse
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_banner():
    """Print startup banner."""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   FOLIOX DOCUMENT SCANNER BOT                             ║
    ║   ──────────────────────────────                          ║
    ║   AI-powered BOL document scanning for Slack              ║
    ║                                                           ║
    ║   Commands:                                               ║
    ║     /scan <url>  - Scan document from URL                 ║
    ║     Upload file  - Auto-scan uploaded images              ║
    ║                                                           ║
    ║   Extracted Fields:                                       ║
    ║     • Bill To, Ship To, BOL Number                        ║
    ║     • Site Name, Gross/Net Gallons                        ║
    ║     • Product, Terminal, Carrier                          ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)


def check_environment():
    """Check required environment variables."""
    from dotenv import load_dotenv
    load_dotenv()

    required = [
        ("SLACK_BOT_TOKEN", "Slack Bot User OAuth Token"),
        ("SLACK_SIGNING_SECRET", "Slack App signing secret"),
        ("ANTHROPIC_API_KEY", "Anthropic API key"),
    ]

    missing = []
    for var, description in required:
        if not os.environ.get(var):
            missing.append(f"  - {var}: {description}")

    if missing:
        print("\nMissing required environment variables:")
        print("\n".join(missing))
        print("\nPlease set these in your .env file or environment.")
        print("See .env.example for configuration template.")
        sys.exit(1)

    print("Environment configuration validated.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Foliox Document Scanner Bot - Slack BOL document scanning"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port to listen on (default: 3000)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )

    args = parser.parse_args()

    print_banner()
    check_environment()

    # Import and run server
    from src.slack_bot_server import run_server

    try:
        run_server(host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
