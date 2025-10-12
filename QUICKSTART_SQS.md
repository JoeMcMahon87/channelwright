# Quick Start: SQS Architecture

## What's New?

The bot now uses **Amazon SQS** for asynchronous channel creation with real-time progress updates!

### Before
- ⏱️ 5-6 second response time
- ⚠️ Discord timeout warnings
- ❌ No progress feedback

### After
- ⚡ < 1 second response time
- ✅ No timeout warnings
- 📊 Real-time progress bar
- 🎯 Professional user experience

## Deploy in 3 Steps

### Step 1: Update .env

Add your Discord credentials to `.env`:

```bash
DISCORD_PUBLIC_KEY=your_public_key_here
DISCORD_BOT_TOKEN=your_bot_token_here
LAMBDA_FUNCTION_NAME=discord_channelwright_bot
AWS_REGION=us-east-1
```

### Step 2: Deploy

Run the deployment script:

```bash
./scripts/deploy-sqs.sh
```

This will:
- ✅ Create SQS queue
- ✅ Create worker Lambda
- ✅ Update main Lambda
- ✅ Configure IAM permissions
- ✅ Set up event source mapping

### Step 3: Test

In Discord, run:

```
/add-campaign name: Test Campaign
```

**You'll see:**

1. **Immediate response** (< 1 second):
   ```
   Bot is thinking...
   ```

2. **Progress updates** (every ~1 second):
   ```
   🏗️ Creating Campaign: Test Campaign

   [████████░░░░░░░░░░░░] 40% (4/10)

   ✅ Created: session-notes (Text)
   ```

3. **Final result** (after 5-10 seconds):
   ```
   ✅ Campaign Created: Test Campaign

   **Role:** Test Campaign Members

   **Created 10 channels:**

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

## How It Works

```
User runs /add-campaign
         ↓
Main Lambda creates role & category (1s)
         ↓
Main Lambda queues 10 tasks to SQS
         ↓
Main Lambda returns "thinking..." ← YOU SEE THIS INSTANTLY
         ↓
Worker Lambda processes tasks one by one
         ↓
Each task updates progress bar ← YOU SEE PROGRESS
         ↓
Final task shows complete list ← YOU SEE SUCCESS
```

## Architecture Components

### Main Lambda (`bot.py`)
- Receives Discord interactions
- Creates role & category
- Queues channel tasks
- Returns immediately

### SQS Queue
- Stores channel creation tasks
- Ensures reliable processing
- Auto-scales with demand

### Worker Lambda (`worker.py`)
- Triggered by SQS
- Creates channels one by one
- Updates progress in real-time
- Handles errors gracefully

## Monitoring

### View Logs

**Main Lambda:**
```bash
aws logs tail /aws/lambda/discord_channelwright_bot --follow
```

**Worker Lambda:**
```bash
aws logs tail /aws/lambda/discord_channelwright_worker --follow
```

### Check Queue

```bash
aws sqs get-queue-attributes \
  --queue-url $(aws cloudformation describe-stacks \
    --stack-name channelwright-sqs-stack \
    --query 'Stacks[0].Outputs[?OutputKey==`QueueUrl`].OutputValue' \
    --output text) \
  --attribute-names ApproximateNumberOfMessages
```

## Troubleshooting

### Issue: "Bot didn't respond"

**Cause:** Main Lambda timeout or error before returning type 5

**Solution:**
1. Check main Lambda logs
2. Verify SQS_QUEUE_URL environment variable is set
3. Ensure IAM permissions allow SQS SendMessage

### Issue: Progress bar not updating

**Cause:** Worker Lambda not processing messages

**Solution:**
1. Check worker Lambda logs
2. Verify event source mapping is enabled
3. Check SQS queue for messages

### Issue: Channels not created

**Cause:** Worker Lambda errors or Discord API issues

**Solution:**
1. Check worker Lambda logs for errors
2. Verify bot has "Manage Channels" permission
3. Check Dead Letter Queue for failed messages

## Configuration

### Customize Channels

Edit `config/campaign_channels.yaml`:

```yaml
channels:
  - name: my-custom-channel
    type: text
    gm_only: false
    description: My custom channel
```

Redeploy:
```bash
./scripts/deploy-sqs.sh
```

### Adjust Timeouts

Edit `infrastructure/sqs-worker.yaml`:

```yaml
VisibilityTimeout: 60  # Seconds before message reappears
MessageRetentionPeriod: 3600  # Keep messages for 1 hour
```

## Cost

**For 100 campaigns/month:**
- SQS: ~$0.00 (free tier)
- Lambda: ~$0.03
- **Total: $0.03/month**

Essentially free! 🎉

## Next Steps

1. ✅ Deploy the bot
2. ✅ Test with a campaign
3. ✅ Customize channels
4. ✅ Monitor logs
5. ✅ Enjoy instant responses!

## Support

- 📖 Full docs: `SQS_ARCHITECTURE.md`
- 🔧 Deployment: `scripts/deploy-sqs.sh`
- 🏗️ Infrastructure: `infrastructure/sqs-worker.yaml`
- 👷 Worker code: `src/worker.py`
- 🤖 Main bot: `src/bot.py`

## Comparison

| Metric | Old | New |
|--------|-----|-----|
| Response Time | 5-6s | <1s |
| Timeout Warning | Yes | No |
| Progress Updates | No | Yes |
| User Experience | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**The bot is now production-ready with enterprise-grade architecture!** 🚀
