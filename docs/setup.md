# ChannelWright Setup Guide

This guide will walk you through setting up and deploying the ChannelWright Discord bot.

## Prerequisites

Before you begin, make sure you have:

- **AWS Account** with appropriate permissions
- **Discord Developer Account** and a bot application
- **Terraform** (>= 1.0) installed
- **AWS CLI** configured with your credentials
- **Python 3.11+** for local development
- **Git** for version control

## Step 1: Discord Bot Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application or select an existing one
3. Go to the "Bot" section and create a bot
4. Copy the **Bot Token** (keep this secret!)
5. Note the **Application ID** from the "General Information" section
6. Under "Bot" → "Privileged Gateway Intents", enable:
   - Server Members Intent
   - Message Content Intent

### Required Bot Permissions

Your bot needs the following permissions:
- `Manage Channels` - To create categories and channels
- `Manage Roles` - To create campaign member roles
- `View Channels` - To see existing channels
- `Send Messages` - To respond to commands
- `Use Slash Commands` - To register and use slash commands

## Step 2: Environment Configuration

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <repository-url>
   cd channelwright
   ```

2. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and fill in your values:
   ```bash
   DISCORD_BOT_TOKEN=your_discord_bot_token_here
   DISCORD_APPLICATION_ID=your_discord_application_id_here
   AWS_REGION=us-east-1
   ENVIRONMENT=dev
   ```

4. Export the environment variables:
   ```bash
   source .env
   export DISCORD_BOT_TOKEN
   export DISCORD_APPLICATION_ID
   ```

## Step 3: AWS Configuration

1. Configure AWS CLI if you haven't already:
   ```bash
   aws configure
   ```

2. Verify your AWS credentials:
   ```bash
   aws sts get-caller-identity
   ```

## Step 4: Deploy the Bot

1. Make the deployment script executable:
   ```bash
   chmod +x scripts/deploy.sh scripts/build.sh
   ```

2. Run the deployment:
   ```bash
   ./scripts/deploy.sh dev
   ```

   This will:
   - Build the Lambda deployment package
   - Create AWS infrastructure with Terraform
   - Deploy the bot Lambda function
   - Output the webhook URL

3. Note the webhook URL from the deployment output.

## Step 5: Configure Discord Webhook

1. Go back to the Discord Developer Portal
2. Navigate to your application → "General Information"
3. Set the **Interactions Endpoint URL** to the Lambda function URL from step 4
4. Save the changes

Discord will verify the endpoint by sending a PING request.

## Step 6: Register Slash Commands

1. Make the command registration script executable:
   ```bash
   chmod +x scripts/register-commands.py
   ```

2. Register the commands:
   ```bash
   python3 scripts/register-commands.py
   ```

   This will register the `/begin-campaign` and `/list-campaigns` commands with Discord.

## Step 7: Invite Bot to Server

1. In the Discord Developer Portal, go to "OAuth2" → "URL Generator"
2. Select scopes:
   - `bot`
   - `applications.commands`
3. Select bot permissions:
   - `Manage Channels`
   - `Manage Roles`
   - `View Channels`
   - `Send Messages`
   - `Use Slash Commands`
4. Copy the generated URL and open it in your browser
5. Select your Discord server and authorize the bot

## Step 8: Test the Bot

1. In your Discord server, try the `/begin-campaign` command:
   ```
   /begin-campaign name:My First Campaign
   ```

2. The bot should:
   - Create a new category with the campaign name
   - Create a role called "My First Campaign Members"
   - Create channels based on the default template
   - Set up proper permissions

3. Try the `/list-campaigns` command to see all campaigns in the server.

## Configuration

### Channel Templates

You can customize the channels created for each campaign by editing `config/channel_templates.yaml`. The default template includes:

- **Public channels** (accessible to campaign members):
  - `general` - Text channel for discussion
  - `character-sheets` - Forum for character sheets
  - `session-recaps` - Forum for session summaries
  - `voice-chat` - Voice channel for sessions

- **Private channels** (guild owner and GM only):
  - `gm-notes` - Text channel for GM planning
  - `gm-resources` - Forum for GM resources

### Environment Variables

- `ENVIRONMENT` - Deployment environment (dev, staging, prod)
- `AWS_REGION` - AWS region for deployment
- `DISCORD_BOT_TOKEN` - Your Discord bot token
- `DISCORD_APPLICATION_ID` - Your Discord application ID

## Troubleshooting

### Common Issues

1. **"Application did not respond"** - Check that:
   - The Lambda function is deployed correctly
   - The Discord webhook URL is set correctly
   - The bot token is valid in AWS Systems Manager

2. **"Missing Permissions"** - Ensure the bot has:
   - Manage Channels permission
   - Manage Roles permission
   - Proper role hierarchy (bot role above created roles)

3. **Commands not appearing** - Run the command registration script:
   ```bash
   python3 scripts/register-commands.py
   ```

4. **AWS deployment fails** - Check:
   - AWS credentials are configured
   - You have necessary AWS permissions
   - Environment variables are set

### Logs

Check AWS CloudWatch logs for the Lambda function:
```bash
aws logs tail /aws/lambda/channelwright-bot-dev --follow
```

## Updating the Bot

To update the bot after making changes:

1. Rebuild and redeploy:
   ```bash
   ./scripts/deploy.sh dev
   ```

2. If you changed command definitions, re-register commands:
   ```bash
   python3 scripts/register-commands.py
   ```

## Production Deployment

For production deployment:

1. Use a different environment:
   ```bash
   ./scripts/deploy.sh prod
   ```

2. Consider using Terraform workspaces for better state management
3. Set up proper monitoring and alerting
4. Use a custom domain for the webhook URL
5. Implement proper secret rotation for the bot token
