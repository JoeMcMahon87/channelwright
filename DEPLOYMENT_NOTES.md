# Deployment Notes for /add-campaign Command

## Changes Made

### 1. Bot Code (`src/bot.py`)
- Added `requests` import for Discord API calls
- Added `create_channel_category()` function to create Discord channel categories
- Added `/add-campaign` command handler with:
  - Required `name` parameter extraction
  - Guild ID validation (command only works in servers)
  - Error handling for API failures
  - Ephemeral error messages (only visible to command user)

### 2. Command Registration (`scripts/register_commands.py`)
- Added `/add-campaign` command definition with:
  - Required string parameter: `name`
  - Description: "Create a new campaign channel category"

### 3. Deployment Script (`scripts/deploy.sh`)
- Updated to include `DISCORD_BOT_TOKEN` environment variable
- Both create and update Lambda functions now receive the bot token

### 4. Documentation
- Updated `README.md` with `/add-campaign` usage
- Added "Manage Channels" permission requirement

## Deployment Steps

1. **Update your `.env` file** (if not already present):
   ```bash
   DISCORD_BOT_TOKEN=your_bot_token_here
   ```

2. **Deploy the updated code**:
   ```bash
   ./scripts/deploy.sh
   ```

3. **Register the new command**:
   ```bash
   python3 scripts/register_commands.py
   ```
   
   You should see:
   ```
   ✓ Successfully registered command: /hellobot
   ✓ Successfully registered command: /add-campaign
   ```

4. **Update bot permissions** (if bot is already invited):
   - Go to Discord Developer Portal → OAuth2 → URL Generator
   - Select scopes: `bot`, `applications.commands`
   - Select permissions: `Send Messages`, `Manage Channels`
   - Use the generated URL to re-invite the bot (it will update permissions)

## Testing

After deployment, test in your Discord server:

```
/add-campaign name: My First Campaign
```

Expected response:
```
✅ Created campaign category: **My First Campaign**
```

You should see a new channel category appear in your server's channel list.

## Troubleshooting

### Command not appearing
- Wait 5-10 minutes for Discord to propagate the command
- Restart Discord client
- Verify `register_commands.py` ran successfully

### "Missing Permissions" error
- Ensure bot has "Manage Channels" permission
- Re-invite bot with updated permissions URL

### "Failed to create campaign category" error
- Check Lambda CloudWatch logs: `aws logs tail /aws/lambda/hellobot --follow`
- Verify `DISCORD_BOT_TOKEN` is set in Lambda environment variables
- Ensure bot token is valid and not expired

## Next Steps

The foundation is in place for additional campaign management features:
- Add channels to the campaign category
- Delete campaign categories
- List all campaigns
- Add campaign metadata storage (DynamoDB)
