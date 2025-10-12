# SQS-Based Architecture

## Overview

The bot now uses an **SQS-based asynchronous architecture** to handle channel creation with real-time progress updates.

## Architecture Flow

```
Discord User
    ↓
    /add-campaign
    ↓
API Gateway
    ↓
Main Lambda (bot.py)
    ├─ Creates Role (1s)
    ├─ Creates Category (1s)
    ├─ Queues 10 tasks to SQS
    └─ Returns Type 5 (deferred) ← INSTANT RESPONSE
    ↓
SQS Queue
    ├─ Task 1: Create channel "general"
    ├─ Task 2: Create channel "session-notes"
    ├─ ...
    └─ Task 11: Send completion message
    ↓
Worker Lambda (worker.py) ← Triggered by SQS
    ├─ Creates channel
    ├─ Updates progress bar via webhook
    └─ Repeats for each task
    ↓
Discord Webhook
    └─ Edits original message with progress
```

## Step-by-Step Process

### Step 1: Instant ACK (< 1 second)

**Main Lambda receives `/add-campaign`:**
1. Verifies Discord signature
2. Creates role immediately
3. Creates category immediately  
4. Queues channel creation tasks to SQS
5. **Returns type 5 (deferred response)**

**User sees:** "Bot is thinking..." (no timeout!)

### Step 2: Async Processing (5-10 seconds)

**Worker Lambda processes SQS messages:**
1. Receives message from queue
2. Creates the channel
3. Edits original Discord message with progress bar
4. Deletes message from queue
5. Repeats for next channel

**User sees:** Progress bar updating in real-time:
```
🏗️ Creating Campaign: My Campaign

[████████████░░░░░░░░] 60% (6/10)

✅ Created: character-sheets (Forum)
```

### Step 3: Completion (after all channels)

**Worker Lambda processes completion message:**
1. Builds final summary
2. Edits original message with complete channel list
3. Marks campaign as complete

**User sees:** Final success message with all channels listed

## Components

### 1. Main Lambda (`bot.py`)
- **Function:** `discord_channelwright_bot`
- **Trigger:** API Gateway (Discord webhook)
- **Timeout:** 30 seconds
- **Memory:** 128 MB
- **Responsibilities:**
  - Verify Discord requests
  - Create role & category
  - Queue tasks to SQS
  - Return deferred response

### 2. SQS Queue
- **Name:** `channelwright-tasks`
- **Visibility Timeout:** 60 seconds
- **Message Retention:** 1 hour
- **Purpose:** Store channel creation tasks

### 3. Worker Lambda (`worker.py`)
- **Function:** `discord_channelwright_worker`
- **Trigger:** SQS messages
- **Timeout:** 30 seconds
- **Memory:** 256 MB
- **Batch Size:** 1 (process one channel at a time)
- **Responsibilities:**
  - Create individual channels
  - Update progress via Discord webhook
  - Handle errors gracefully

## Message Format

### Channel Creation Task
```json
{
  "task_type": "create_channel",
  "application_id": "123456789",
  "interaction_token": "abc123...",
  "guild_id": "987654321",
  "channel_config": {
    "name": "general",
    "type": 0,
    "gm_only": false,
    "description": "General discussion"
  },
  "category_id": "111222333",
  "campaign_role_id": "444555666",
  "current": 1,
  "total": 10,
  "campaign_name": "My Campaign"
}
```

### Completion Task
```json
{
  "task_type": "complete",
  "application_id": "123456789",
  "interaction_token": "abc123...",
  "campaign_name": "My Campaign",
  "role_name": "My Campaign Members",
  "created_channels": [
    {"name": "general", "type": "Text", "gm_only": false},
    ...
  ]
}
```

## Progress Bar Implementation

The worker creates a visual progress bar:

```python
def create_progress_bar(current, total, width=20):
    filled = int((current / total) * width)
    bar = "█" * filled + "░" * (width - filled)
    percentage = int((current / total) * 100)
    return f"[{bar}] {percentage}% ({current}/{total})"
```

**Example output:**
```
[████████████████████] 100% (10/10)
```

## Benefits

### 1. No Timeout Issues ✅
- Main Lambda returns in < 2 seconds
- Discord never shows "didn't respond" warning
- User sees immediate acknowledgment

### 2. Real-Time Progress ✅
- User sees each channel being created
- Progress bar shows completion percentage
- Better user experience

### 3. Scalability ✅
- SQS handles any number of channels
- Worker Lambda auto-scales
- Can process multiple campaigns simultaneously

### 4. Reliability ✅
- Failed messages go to Dead Letter Queue
- Automatic retries for transient errors
- Easy to monitor and debug

### 5. Cost Effective ✅
- Pay only for actual processing time
- No idle Lambda waiting
- SQS is very cheap ($0.40 per million requests)

## Deployment

### Deploy Everything
```bash
./scripts/deploy-sqs.sh
```

This script:
1. Creates deployment package
2. Creates/updates CloudFormation stack (SQS + Worker Lambda)
3. Updates main Lambda with SQS integration
4. Updates worker Lambda code
5. Configures IAM permissions

### Manual Steps

#### 1. Create SQS Queue
```bash
aws cloudformation create-stack \
  --stack-name channelwright-sqs-stack \
  --template-body file://infrastructure/sqs-worker.yaml \
  --parameters \
      ParameterKey=DiscordBotToken,ParameterValue=$DISCORD_BOT_TOKEN \
      ParameterKey=MainLambdaArn,ParameterValue=$MAIN_LAMBDA_ARN \
  --capabilities CAPABILITY_NAMED_IAM
```

#### 2. Update Main Lambda
```bash
aws lambda update-function-configuration \
  --function-name discord_channelwright_bot \
  --environment "Variables={...,SQS_QUEUE_URL=$QUEUE_URL}"
```

#### 3. Deploy Worker Lambda
```bash
aws lambda update-function-code \
  --function-name discord_channelwright_worker \
  --zip-file fileb://deployment.zip
```

## Monitoring

### CloudWatch Logs

**Main Lambda:**
```
/aws/lambda/discord_channelwright_bot
```

**Worker Lambda:**
```
/aws/lambda/discord_channelwright_worker
```

### SQS Metrics

Monitor in CloudWatch:
- `NumberOfMessagesSent`
- `NumberOfMessagesReceived`
- `ApproximateAgeOfOldestMessage`
- `NumberOfMessagesDeleted`

### Debugging

**Check queue depth:**
```bash
aws sqs get-queue-attributes \
  --queue-url $QUEUE_URL \
  --attribute-names ApproximateNumberOfMessages
```

**View messages in DLQ:**
```bash
aws sqs receive-message \
  --queue-url $DLQ_URL \
  --max-number-of-messages 10
```

## Error Handling

### Transient Errors
- Worker Lambda automatically retries (SQS default: 3 times)
- Visibility timeout prevents duplicate processing

### Permanent Errors
- After max retries, message moves to Dead Letter Queue
- User sees error message via Discord webhook
- Admin can inspect DLQ for failed tasks

### Discord Webhook Errors
- If webhook fails, message stays in queue
- Will retry on next visibility timeout
- Eventually moves to DLQ if persistent

## Cost Estimate

**For 100 campaigns/month (1000 channels):**
- SQS: $0.40 per million requests = **$0.00**
- Worker Lambda: 1000 invocations × 2s × $0.0000166667/GB-second = **$0.03**
- Main Lambda: 100 invocations × 2s × $0.0000166667/GB-second = **$0.00**

**Total: ~$0.03/month** (essentially free!)

## Comparison: Old vs New

| Feature | Old (Threading) | New (SQS) |
|---------|----------------|-----------|
| Response Time | 5-6 seconds | < 1 second |
| Discord Warning | ❌ Yes | ✅ No |
| Progress Updates | ❌ No | ✅ Yes |
| Scalability | ❌ Limited | ✅ Unlimited |
| Reliability | ⚠️ Fair | ✅ Excellent |
| Monitoring | ⚠️ Basic | ✅ Comprehensive |
| Cost | $0.00 | $0.03 |

## Future Enhancements

1. **Batch Processing**: Process multiple channels per worker invocation
2. **Priority Queue**: VIP users get faster processing
3. **Rate Limiting**: Prevent Discord API rate limits
4. **Rollback**: Undo campaign creation if errors occur
5. **Webhooks**: Notify external systems when campaigns are created
