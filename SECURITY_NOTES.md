# Security Notes

## Bot Token Security

### ⚠️ Important: Token Exposure
If your Discord bot token is ever exposed in logs, terminal output, or version control, Discord will automatically invalidate it for security reasons. This results in 401 Unauthorized errors when trying to use the token.

### Deploy Script Security Improvements
The deployment script has been updated to **hide sensitive environment variables** from output:

- ✅ Environment variables (DISCORD_BOT_TOKEN, DISCORD_PUBLIC_KEY) are no longer displayed in AWS CLI output
- ✅ Uses `--query` parameter to filter AWS responses to only show non-sensitive data
- ✅ Adds clear messages when setting environment variables: "🔐 Setting environment variables (sensitive data hidden)..."

### If Your Token Was Compromised

1. **Regenerate the bot token**:
   - Go to https://discord.com/developers/applications
   - Select your application
   - Go to "Bot" tab
   - Click "Reset Token"
   - Copy the new token immediately

2. **Update your `.env` file**:
   ```bash
   nano .env
   # Update DISCORD_BOT_TOKEN with the new token
   ```

3. **Redeploy to update Lambda**:
   ```bash
   ./scripts/deploy.sh
   ```
   
   The new deploy script will hide the token from output.

4. **Register commands**:
   ```bash
   source ../venv/bin/activate
   python3 scripts/register_commands.py
   ```

### Best Practices

1. **Never commit `.env` files** to version control (already in `.gitignore`)
2. **Regenerate tokens** if you suspect they've been exposed
3. **Use environment variables** for all sensitive data
4. **Review logs** before sharing terminal output
5. **Rotate tokens periodically** as a security best practice

### What the Deploy Script Now Shows

**Before (insecure)**:
```json
{
  "Environment": {
    "Variables": {
      "DISCORD_BOT_TOKEN": "MTQyNjYzODQxOTcyMjg5NTM4MA.GTkn5r...",
      "DISCORD_PUBLIC_KEY": "6e935a2ed67a71754bf20cf901cba943..."
    }
  }
}
```

**After (secure)**:
```json
{
  "FunctionName": "discord_channelwright_bot",
  "Runtime": "python3.11",
  "LastModified": "2025-10-12T00:13:20.000+0000",
  "State": "Active"
}
```

Environment variables are still set correctly in Lambda, but they're not displayed in the terminal output.
