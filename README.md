# Gmail-Slack Cost Monitor Agent

An automated agent that monitors your Gmail for cost data emails, sends Slack notifications when they arrive, and replies to customers with daily cost trend analysis.

## Features

- **Gmail Monitoring**: Continuously polls for new emails matching configurable subject patterns
- **Slack Notifications**: Sends formatted alerts when cost data is received
- **Trend Analysis**: Compares current costs against historical data
- **Auto-Reply**: Automatically responds to customers with detailed trend reports

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
3. Name your app and select your workspace
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

# Agent Configuration
COST_EMAIL_SUBJECT_PATTERN=Cost Data|Cost Report|Daily Costs
POLL_INTERVAL=60
WATCH_SENDER_EMAIL=
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
1. Poll Gmail every 60 seconds (configurable)
2. Look for unread emails matching the subject pattern
3. When a matching email is found:
   - Send a Slack notification to your channel
   - Parse cost data from the email body
   - Calculate trends against historical data
   - Send a trend summary to Slack
   - Reply to the email with a detailed trend report
   - Mark the email as read

### Expected Email Format

The agent can parse cost data from emails in formats like:

```
Compute: $1,234.56
Storage: $456.78
Network: $123.45
Database: $789.00
```

Or:

```
Compute costs - $1234.56
Storage costs: $456.78
```

If no cost data is found in the email, sample data will be used for demonstration.

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_CREDENTIALS_PATH` | Path to OAuth credentials JSON | `credentials.json` |
| `SLACK_BOT_TOKEN` | Slack bot OAuth token | Required |
| `SLACK_CHANNEL_ID` | Slack channel for notifications | Required |
| `COST_EMAIL_SUBJECT_PATTERN` | Regex pattern for email subjects | `Cost Data\|Cost Report\|Daily Costs` |
| `POLL_INTERVAL` | Seconds between email checks | `60` |
| `WATCH_SENDER_EMAIL` | Only process emails from this sender | All senders |

## Project Structure

```
.
├── main.py                 # Entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Example environment config
├── .gitignore             # Git ignore rules
├── README.md              # This file
└── src/
    ├── __init__.py
    ├── agent.py           # Main agent orchestrator
    ├── gmail_client.py    # Gmail API client
    ├── slack_client.py    # Slack API client
    └── cost_processor.py  # Cost parsing and trend analysis
```

## Extending the Agent

### Custom Cost Categories

Edit `src/cost_processor.py` to add new cost categories in the `_normalize_category` method.

### Historical Data Integration

Replace the sample data in `CostProcessor.__init__` with a database connection to use real historical data.

### Different Notification Formats

Modify `SlackClient.send_cost_alert` and `send_trend_summary` to customize Slack message formats.

## Troubleshooting

### "Credentials file not found"
Download the OAuth credentials from Google Cloud Console and place it in the project root as `credentials.json`.

### "Token has been expired or revoked"
Delete `token.json` and run the agent again to re-authenticate.

### Slack messages not appearing
- Verify the bot token starts with `xoxb-`
- Ensure the bot has been added to the channel
- Check that the channel ID is correct (starts with `C`)

## License

MIT
