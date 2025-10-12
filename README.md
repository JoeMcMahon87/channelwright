# HelloBot - Discord Interactions Bot

A simple Discord bot using the `discord-interactions` library that responds to `/hellobot` with a personalized greeting.

## Features

- **Serverless Architecture**: Runs on AWS Lambda for cost-effective hosting
- **Slash Commands**: 
  - `/hellobot` - Bot replies with "Hello {username}! 👋"
  - `/add-campaign <name>` - Creates a complete campaign setup with category, role, and channels
- **Discord Interactions**: Uses official Discord interactions for fast, reliable responses
- **Easy Deployment**: Simple scripts for local testing and AWS deployment

## Project Structure

```
hellobot/
├── src/
│   └── bot.py                 # Main Lambda handler
├── scripts/
│   ├── register_commands.py   # Register slash commands with Discord
│   ├── deploy.sh              # Deploy to AWS Lambda
│   └── test_local.py          # Local testing script
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variable template
└── README.md                 # This file
```

## Prerequisites

1. **Discord Application**:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Go to "Bot" section and create a bot
   - Copy the Bot Token
   - Go to "General Information" and copy Application ID and Public Key

2. **AWS Account** (for deployment):
   - AWS CLI configured with credentials
   - Lambda execution role created

3. **Python 3.9+**

## Setup

### 1. Install Dependencies

```bash
cd hellobot
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Discord credentials
```

Required environment variables:
- `DISCORD_APP_ID`: Your Discord Application ID
- `DISCORD_BOT_TOKEN`: Your Discord Bot Token
- `DISCORD_PUBLIC_KEY`: Your Discord Public Key
- `AWS_REGION`: AWS region for Lambda (e.g., us-east-1)
- `LAMBDA_FUNCTION_NAME`: Name for your Lambda function

### 3. Test Locally

```bash
python scripts/test_local.py
```

This runs unit tests to verify the bot logic works correctly.

### 4. Deploy to AWS Lambda

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### 5. Set Up API Gateway

1. Create a new API Gateway (HTTP API or REST API)
2. Create a POST route pointing to your Lambda function
3. Deploy the API and copy the endpoint URL

### 6. Configure Discord

1. Go to your Discord Application in the Developer Portal
2. Navigate to "General Information"
3. Set "Interactions Endpoint URL" to your API Gateway URL
4. Discord will send a PING request to verify the endpoint

### 7. Register Slash Commands

```bash
python scripts/register_commands.py
```

This registers the `/hellobot` command with Discord. Commands may take a few minutes to appear.

### 8. Invite Bot to Server

1. Go to "OAuth2" → "URL Generator" in Discord Developer Portal
2. Select scopes: `bot`, `applications.commands`
3. Select bot permissions: 
   - `Send Messages`
   - `Manage Channels` (required for `/add-campaign`)
   - `Manage Roles` (required for `/add-campaign`)
4. Copy the generated URL and open it in a browser
5. Select a server and authorize the bot

## Usage

Once deployed and configured, use the bot in Discord:

### /hellobot
```
/hellobot
```

The bot will respond with:
```
Hello YourUsername! 👋
```

### /add-campaign
```
/add-campaign name: My Campaign
```

The bot will create a complete campaign setup asynchronously:
1. **Channel Category** with the campaign name
2. **Role** named "[Campaign Name] Members"
3. **Default Channels** (configured in `config/campaign_channels.yaml`):
   - **Text Channels**: general, session-notes
   - **Forum Channels**: character-sheets, lore-and-worldbuilding
   - **Voice Channels**: voice-chat
   - **GM-Only Channels** 🔒: gm-notes (text), gm-planning (forum)

**Channel Permissions:**
- Regular channels: Visible to campaign role members
- GM-only channels 🔒: Visible only to:
  - Guild owner
  - Administrator roles
  - "GM" role (if it exists)

**Initial Response:**
The bot will show a "thinking" indicator while creating channels.

**Follow-up Message (after creation completes):**
```
✅ Campaign Created: My Campaign

**Role:** My Campaign Members

**Channels:**
📝 Text:
  • general
  • session-notes
  • gm-notes 🔒
🔊 Voice:
  • voice-chat
💬 Forum:
  • character-sheets
  • lore-and-worldbuilding
  • gm-planning 🔒
```

**Note**: 
- The bot needs "Manage Channels" and "Manage Roles" permissions
- Creating 10+ channels takes 5-6 seconds, so Discord may show "The application did not respond" warning
- **This is normal** - the channels are still created successfully, just check your server!
- You can customize channels by editing `config/campaign_channels.yaml`
- GM-only channels (marked 🔒) require manual permission setup - see `GM_CHANNELS_SETUP.md`

## How It Works

1. **Discord Interactions**: Discord sends HTTP POST requests to your API Gateway endpoint
2. **Lambda Handler**: AWS Lambda receives the request and processes it
3. **Verification**: The `discord-interactions` library verifies the request signature
4. **Response**: Bot returns a JSON response that Discord displays to the user

### Key Components

- **`bot.py`**: Main Lambda handler that processes Discord interactions
  - Handles PING requests for endpoint verification
  - Processes `/hellobot` command and extracts username
  - Returns formatted response to Discord

- **`register_commands.py`**: Registers slash commands with Discord API
  - Uses Discord's REST API to create global commands
  - Commands become available in all servers with the bot

## Development

### Local Testing

The bot includes a local testing mode:

```python
python src/bot.py
```

This simulates Discord interactions without requiring deployment.

### Adding New Commands

1. Update `bot.py` to handle the new command name
2. Add command definition to `register_commands.py`
3. Run `python scripts/register_commands.py` to register

Example:
```python
# In register_commands.py
commands = [
    {
        "name": "hellobot",
        "description": "Get a friendly hello from the bot!",
        "type": 1
    },
    {
        "name": "goodbye",
        "description": "Say goodbye",
        "type": 1
    }
]

# In bot.py
if command_name == 'goodbye':
    return {
        'statusCode': 200,
        'body': json.dumps({
            'type': InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            'data': {
                'content': f'Goodbye {username}! 👋'
            }
        })
    }
```

## Cost Estimation

AWS Lambda Free Tier includes:
- 1 million requests per month
- 400,000 GB-seconds of compute time

For a small bot, this should stay within free tier limits.

## Troubleshooting

### "Invalid Interactions Endpoint URL"
- Ensure your API Gateway endpoint is publicly accessible
- Verify Lambda function has correct DISCORD_PUBLIC_KEY environment variable
- Check Lambda logs in CloudWatch for errors

### Commands Not Appearing
- Wait 5-10 minutes after registration
- Try restarting Discord client
- Verify bot has `applications.commands` scope

### Bot Not Responding
- Check Lambda CloudWatch logs for errors
- Verify API Gateway is correctly routing to Lambda
- Ensure Lambda has proper IAM permissions

## Security

- **Request Verification**: All requests are verified using Discord's public key
- **Environment Variables**: Sensitive credentials stored in environment variables
- **AWS IAM**: Lambda uses IAM roles for secure AWS service access

## Resources

- [Discord Interactions Documentation](https://discord.com/developers/docs/interactions/receiving-and-responding)
- [discord-interactions Library](https://github.com/discord/discord-interactions-python)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)

## License

MIT License - Feel free to use and modify for your own projects!
