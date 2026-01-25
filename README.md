# OPIS Fuel Price Monitor Agent

An automated agent that monitors Gmail for OPIS (Oil Price Information Service) fuel pricing emails, sends Slack notifications when new pricing data arrives, calculates price trends, and replies with detailed trend analysis.

## Features

- **Gmail Monitoring**: Continuously polls for OPIS pricing emails from `opisadmin@opisnet.com`
- **OPIS Data Parsing**: Parses complex OPIS wholesale rack pricing data including:
  - Multiple locations (e.g., AMARILLO, TX; LUBBOCK, TX)
  - Multiple fuel products (Gasoline, Diesel, Biodiesel, Jet fuel)
  - Supplier prices (Valero, PSX, DKTS, Cenex, XOM, Chevron)
  - Rack averages, spot prices, branded/unbranded prices
  - Retail pricing data
- **Slack Notifications**: Sends formatted alerts with fuel price summaries
- **Trend Analysis**: Tracks price history and calculates day-over-day and weekly trends
- **Auto-Reply**: Automatically responds with detailed trend reports

## Prerequisites

- Python 3.10+
- Google Cloud account with Gmail API enabled
- Slack workspace with a bot configured

## Setup

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd claude-test
pip install -r requirements.txt
```

### 2. Set Up Google Gmail API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop app" as the application type
   - Download the credentials JSON file
   - Rename it to `credentials.json` and place it in the project root

### 3. Set Up Slack Bot

1. Go to [Slack API](https://api.slack.com/apps)
2. Click "Create New App" > "From scratch"
3. Name your app (e.g., "OPIS Price Monitor") and select your workspace
4. Go to "OAuth & Permissions"
5. Add these Bot Token Scopes:
   - `chat:write` - Send messages
   - `chat:write.public` - Send messages to channels the bot isn't in
6. Install the app to your workspace
7. Copy the "Bot User OAuth Token" (starts with `xoxb-`)
8. Find your channel ID:
   - Right-click on the channel in Slack
   - Select "View channel details"
   - The channel ID is at the bottom (starts with `C`)

### 4. Configure Environment

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Gmail Configuration
GOOGLE_CREDENTIALS_PATH=credentials.json

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_CHANNEL_ID=C0123456789

# Agent Configuration (defaults are set for OPIS emails)
COST_EMAIL_SUBJECT_PATTERN=OPIS Wholesale|OPIS Spot
POLL_INTERVAL=60
WATCH_SENDER_EMAIL=opisadmin@opisnet.com

# Price history file
PRICE_HISTORY_FILE=price_history.json
```

### 5. First Run - Gmail Authentication

On first run, the agent will open a browser window for Google OAuth authentication:

```bash
python main.py
```

- Log in with your Google account
- Grant the requested permissions
- The token will be saved locally for future runs

## Usage

### Running the Agent

```bash
python main.py
```

The agent will:
1. Poll Gmail every 60 seconds for new OPIS emails
2. When an OPIS email is found:
   - Send a Slack notification: "OPIS Fuel Pricing Data Received"
   - Parse all locations and fuel products from the email
   - Calculate price trends against historical data
   - Save prices to history for future trend analysis
   - Send a fuel price summary to Slack
   - Reply to the email with a detailed trend report
   - Mark the email as read

### Expected Email Format

The agent parses OPIS wholesale rack pricing emails with this format:

```
AMARILLO, TX                                           2026-01-23 09:00:06 EST
                   **OPIS GROSS CONV. CLEAR PRICES**                   9.0 RVP
                                                                Move
             Terms  Unl     Move   Mid     Move   Pre     Move  Date  Time
Valero     b 1-10  208.03  - 1.43  -- --   -- --  -- --   -- -- 01/22 18:00
PSX        b 1-10  211.62  - 3.50  -- --   -- -- 265.96  - 3.50 01/22 18:00
...
LOW RACK           208.03          -- --         265.96
HIGH RACK          233.60          -- --         286.60
RACK AVG           221.01          -- --         276.28
```

### Parsed Data

The agent extracts:
- **Locations**: AMARILLO, TX; LUBBOCK, TX; etc.
- **Products**:
  - Conventional Clear Gasoline
  - CBOB Ethanol (10%)
  - Ultra Low Sulfur Diesel
  - ULS Red Dye Diesel
  - Winter Diesel variants
  - Specialty Distillate (Jet)
  - Biodiesel (B0-5, B2, B5 SME)
- **Prices**: Rack LOW/HIGH/AVG, Spot prices, Branded/Unbranded averages
- **Retail**: Average and low retail prices (with/without tax)

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_CREDENTIALS_PATH` | Path to OAuth credentials JSON | `credentials.json` |
| `SLACK_BOT_TOKEN` | Slack bot OAuth token | Required |
| `SLACK_CHANNEL_ID` | Slack channel for notifications | Required |
| `COST_EMAIL_SUBJECT_PATTERN` | Regex pattern for email subjects | `OPIS Wholesale\|OPIS Spot` |
| `POLL_INTERVAL` | Seconds between email checks | `60` |
| `WATCH_SENDER_EMAIL` | Sender email to filter | `opisadmin@opisnet.com` |
| `PRICE_HISTORY_FILE` | JSON file for price history | `price_history.json` |

## Project Structure

```
.
├── main.py                 # Entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Example environment config
├── .gitignore             # Git ignore rules
├── README.md              # This file
├── price_history.json     # Price history (auto-created)
└── src/
    ├── __init__.py
    ├── agent.py           # Main agent orchestrator
    ├── gmail_client.py    # Gmail API client
    ├── slack_client.py    # Slack notification client
    ├── cost_processor.py  # Fuel price processor & trend analysis
    └── opis_parser.py     # OPIS email format parser
```

## Sample Output

### Slack Notification (Receipt)
```
OPIS Fuel Pricing Data Received
Report Date: 2026-01-23
Received: Fri, 23 Jan 2026 08:02:00
From: opisadmin@opisnet.com
Locations: AMARILLO, TX, LUBBOCK, TX
```

### Slack Price Summary
```
Fuel Price Trends - 2026-01-23

AMARILLO, TX
↓ Gasoline: 221.01 cpg (-2.35)
↓ CBOB Ethanol (10%): 177.72 cpg (-2.88)
↓ ULS Diesel: 232.73 cpg (-1.89)
↓ ULS Red Dye Diesel: 233.87 cpg (-2.01)

Market Insights:
• Largest decrease: CBOB Ethanol in AMARILLO, TX (-2.88 cpg)
• Overall market trending LOWER today.
```

### Email Reply
```
OPIS Fuel Price Trends Report - 2026-01-23
============================================================

Location: AMARILLO, TX
------------------------------------------------------------

Product                               Rack Avg     Change        %
-----------------------------------------------------------------
Conventional Clear Gasoline             221.01      -2.35   -1.05% (DOWN)
CBOB Ethanol (10%)                      177.72      -2.88   -1.60% (DOWN)
Ultra Low Sulfur Diesel                 232.73      -1.89   -0.81% (DOWN)
ULS Red Dye Diesel                      233.87      -2.01   -0.85% (DOWN)

MARKET INSIGHTS
----------------------------------------
  * Largest decrease: CBOB Ethanol (10%) in AMARILLO, TX (-2.88 cpg)
  * Overall market trending LOWER today.
```

## Extending the Agent

### Adding More Locations

The parser automatically handles any locations present in the OPIS email format.

### Adding Product Types

Edit `src/opis_parser.py` to add patterns for new product types in `PRODUCT_PATTERNS`.

### Database Integration

Replace `price_history.json` with a database by modifying `_load_history` and `_save_history` in `src/cost_processor.py`.

### Custom Slack Formatting

Modify `src/slack_client.py` methods `send_opis_alert` and `send_fuel_price_summary` to customize message formats.

## Troubleshooting

### "Credentials file not found"
Download the OAuth credentials from Google Cloud Console and place it in the project root as `credentials.json`.

### "Token has been expired or revoked"
Delete `token.json` and run the agent again to re-authenticate.

### Slack messages not appearing
- Verify the bot token starts with `xoxb-`
- Ensure the bot has been added to the channel
- Check that the channel ID is correct (starts with `C`)

### OPIS data not parsing correctly
- Check that the email body matches the expected OPIS format
- Review logs for parsing errors
- The parser expects the standard OPIS wholesale rack format

## License

MIT
