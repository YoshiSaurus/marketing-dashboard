#!/usr/bin/env python3
"""Main entry point for the Foliox AI Marketing Lead Agent.

Usage:
    # Run the full agent (scan loop + Slack interaction server)
    python marketing_main.py

    # Run a single scan cycle
    python marketing_main.py --once

    # Run only the server (no background scanning, trigger via /scan endpoint)
    python marketing_main.py --server-only
"""

import os
import sys

from dotenv import load_dotenv


def main():
    """Initialize and run the AI Marketing Lead agent."""
    load_dotenv()

    # Validate required configuration
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    slack_webhook = os.getenv("MARKETING_SLACK_WEBHOOK_URL") or os.getenv("SLACK_WEBHOOK_URL")

    if not anthropic_key:
        print("Error: ANTHROPIC_API_KEY is required. Set it in .env file.")
        sys.exit(1)

    if not slack_webhook:
        print("Error: MARKETING_SLACK_WEBHOOK_URL (or SLACK_WEBHOOK_URL) is required.")
        sys.exit(1)

    from src.marketing.marketing_agent import MarketingAgent

    agent = MarketingAgent(
        anthropic_api_key=anthropic_key,
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        banana_api_key=os.getenv("BANANA_API_KEY"),
        google_search_api_key=os.getenv("GOOGLE_SEARCH_API_KEY") or os.getenv("GEMINI_API_KEY"),
        google_search_cx=os.getenv("GOOGLE_SEARCH_CX"),
        slack_webhook_url=slack_webhook,
        slack_bot_token=os.getenv("SLACK_BOT_TOKEN"),
        slack_app_token=os.getenv("SLACK_APP_TOKEN"),
        website_api_url=os.getenv("WEBSITE_API_URL"),
        website_api_key=os.getenv("WEBSITE_API_KEY"),
        linkedin_access_token=os.getenv("LINKEDIN_ACCESS_TOKEN"),
        linkedin_org_id=os.getenv("LINKEDIN_ORG_ID"),
        scan_interval=int(os.getenv("MARKETING_SCAN_INTERVAL", "3600")),
        num_suggestions=int(os.getenv("MARKETING_NUM_SUGGESTIONS", "3")),
        output_dir=os.getenv("MARKETING_OUTPUT_DIR", "marketing_output"),
    )

    # Handle CLI flags
    if "--once" in sys.argv:
        print("Running single scan cycle...")
        suggestions = agent.run_scan_cycle()
        print(f"Generated {len(suggestions)} content suggestions.")
        return

    if "--server-only" in sys.argv:
        from src.marketing.server import create_marketing_app
        port = int(os.getenv("MARKETING_SERVER_PORT", "3001"))
        app = create_marketing_app(agent)
        print(f"Starting server on port {port} (no background scanning)...")
        app.run(host="0.0.0.0", port=port, debug=False)
        return

    # Default: run full server with background scanning
    from src.marketing.server import run_marketing_server
    port = int(os.getenv("MARKETING_SERVER_PORT", "3001"))
    run_marketing_server(port=port)


if __name__ == "__main__":
    main()
