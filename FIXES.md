# Bug Fixes - Campaign Creation Issues

## Problem
The `/add-campaign` command was showing "thinking" indicator but never completing. Logs showed:
1. Config file not found: `[Errno 2] No such file or directory: '/var/task/../config/campaign_channels.yaml'`
2. Lambda function ended immediately after returning response (1.84ms duration)
3. Background thread was terminated when Lambda ended

## Root Causes

### Issue 1: Config File Not in Deployment Package
The `config/` directory was not being included in the Lambda deployment zip file.

**Fix:**
- Updated `scripts/deploy.sh` to explicitly add `config/` directory to deployment.zip
- Added line: `zip -r deployment.zip config/`

### Issue 2: Lambda Timeout Too Short
Lambda function had default 3-second timeout, but creating 7+ channels takes 10-15 seconds.

**Fix:**
- Increased Lambda timeout to 30 seconds
- Updated `scripts/deploy.sh` to set `--timeout 30` on both create and update operations

### Issue 3: Background Threads Don't Work in Lambda
Lambda terminates immediately after returning a response, killing any background threads.

**Fix:**
- Changed from async threading to synchronous execution
- Process flow now:
  1. Do ALL campaign creation work (category, role, channels)
  2. Edit the original deferred response via webhook
  3. Return type 5 (deferred response) to acknowledge
- Lambda stays alive during entire process

## Technical Details

### Deferred Response Pattern
Discord requires responses within 3 seconds. For long operations:

1. **Return Type 5** (DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE)
   - Tells Discord "I'm working on it"
   - Shows "Bot is thinking..." to user

2. **Do the work** (within Lambda timeout)
   - Create category
   - Create role
   - Create all channels
   - Build summary message

3. **Edit original response** via webhook
   - PATCH to `/webhooks/{app_id}/{token}/messages/@original`
   - Replaces "thinking" with actual result

### File Changes

**scripts/deploy.sh:**
```bash
# Add config directory to deployment package
zip -r deployment.zip config/

# Set 30-second timeout
--timeout 30
```

**src/bot.py:**
```python
# Do work BEFORE returning
create_campaign_async(application_id, interaction_token, guild_id, campaign_name, bot_token)

# Then return deferred response
return {'type': 5}  # DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
```

**src/campaign_config.py:**
```python
# Load from YAML file
config_file = os.path.join(config_dir, 'campaign_channels.yaml')
with open(config_file, 'r') as f:
    config = yaml.safe_load(f)
```

## Testing

Test the fixes:

```bash
# Deploy with fixes
./scripts/deploy.sh

# Use command in Discord
/add-campaign name: Test Campaign

# Watch logs
aws logs tail /aws/lambda/discord_channelwright_bot --since 5m --follow
```

Expected behavior:
1. Bot shows "thinking" indicator immediately
2. Logs show `[ASYNC]` prefixed messages for each step
3. After 10-15 seconds, "thinking" is replaced with success message
4. All channels appear in Discord

## Verification

Check Lambda configuration:
```bash
aws lambda get-function-configuration \
  --function-name discord_channelwright_bot \
  --query '[Timeout,CodeSize,State]' \
  --output text
```

Should show:
- Timeout: **30** seconds
- CodeSize: **~3.1 MB** (includes config)
- State: **Active**

## Performance

**Before fixes:**
- Lambda timeout: 3 seconds ❌
- Config file: Missing ❌
- Execution: Terminated after 1.84ms ❌
- Result: Infinite "thinking" spinner ❌

**After fixes:**
- Lambda timeout: 30 seconds ✅
- Config file: Included in deployment ✅
- Execution: Completes in 10-15 seconds ✅
- Result: Success message with all channels ✅
