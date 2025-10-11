# HelloBot Quick Start Guide

Get your HelloBot running in 10 minutes!

## Step 1: Create Discord Application (2 minutes)

1. Go to https://discord.com/developers/applications
2. Click "New Application"
3. Name it "HelloBot" and click "Create"
4. Go to "Bot" tab → Click "Add Bot" → Confirm
5. Copy these values (you'll need them):
   - **Application ID**: From "General Information" tab
   - **Public Key**: From "General Information" tab
   - **Bot Token**: From "Bot" tab (click "Reset Token" if needed)

## Step 2: Set Up Project (1 minute)

```bash
cd /home/joemcmahon/projects/hellobot

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # or use your favorite editor
```

Edit `.env` with your Discord values:
```
DISCORD_APP_ID=your_application_id_here
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_PUBLIC_KEY=your_public_key_here
AWS_REGION=us-east-1
LAMBDA_FUNCTION_NAME=hellobot
```

## Step 3: Test Locally (1 minute)

```bash
python scripts/test_local.py
```

You should see:
```
✓ PING test passed
✓ /hellobot test passed
✓ Member context test passed
✅ All tests passed!
```

## Step 4: Deploy to AWS (3 minutes)

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

**Note**: You need an IAM role named `lambda-execution-role` with Lambda execution permissions. If you don't have one:

```bash
# Create IAM role (one-time setup)
aws iam create-role \
  --role-name lambda-execution-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach basic execution policy
aws iam attach-role-policy \
  --role-name lambda-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

## Step 5: Create API Gateway (2 minutes)

### Option A: AWS Console
1. Go to API Gateway in AWS Console
2. Click "Create API" → "HTTP API" → "Build"
3. Click "Add integration" → "Lambda" → Select your `hellobot` function
4. Name it "hellobot-api" → Click "Next"
5. Leave route as "ANY /" → Click "Next"
6. Leave stage as "$default" → Click "Next"
7. Click "Create"
8. **Copy the Invoke URL** (looks like: `https://abc123.execute-api.us-east-1.amazonaws.com`)

### Option B: AWS CLI
```bash
# Get Lambda ARN
LAMBDA_ARN=$(aws lambda get-function --function-name hellobot --query 'Configuration.FunctionArn' --output text)

# Create API
API_ID=$(aws apigatewayv2 create-api \
  --name hellobot-api \
  --protocol-type HTTP \
  --target "$LAMBDA_ARN" \
  --query 'ApiId' \
  --output text)

# Get API endpoint
aws apigatewayv2 get-api --api-id "$API_ID" --query 'ApiEndpoint' --output text
```

## Step 6: Configure Discord Endpoint (1 minute)

1. Go back to Discord Developer Portal
2. Go to your HelloBot application → "General Information"
3. Find "Interactions Endpoint URL"
4. Paste your API Gateway URL
5. Click "Save Changes"

Discord will send a PING request to verify. If successful, you'll see a green checkmark!

## Step 7: Register Commands (1 minute)

```bash
python scripts/register_commands.py
```

You should see:
```
✓ Successfully registered command: /hellobot
```

## Step 8: Invite Bot to Server (1 minute)

1. In Discord Developer Portal → "OAuth2" → "URL Generator"
2. Select scopes:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Select bot permissions:
   - ✅ `Send Messages`
4. Copy the generated URL at the bottom
5. Open URL in browser and select a server
6. Click "Authorize"

## Step 9: Test It! (30 seconds)

In your Discord server, type:
```
/hellobot
```

The bot should respond:
```
Hello YourUsername! 👋
```

## 🎉 Success!

Your HelloBot is now live and responding to commands!

## Troubleshooting

### "Invalid Interactions Endpoint URL"
- Wait 30 seconds and try saving again
- Check Lambda CloudWatch logs for errors
- Verify DISCORD_PUBLIC_KEY is set correctly in Lambda environment variables

### Commands not showing up
- Wait 5-10 minutes (Discord caches commands)
- Restart Discord client
- Check bot has `applications.commands` scope

### Bot not responding
- Check Lambda logs: `aws logs tail /aws/lambda/hellobot --follow`
- Verify API Gateway is routing to Lambda
- Test Lambda directly in AWS Console

## Next Steps

- Add more commands by editing `src/bot.py` and `scripts/register_commands.py`
- Add command options (parameters) to `/hellobot`
- Implement buttons and select menus
- Add database integration for persistent data

## Need Help?

Check the full README.md for detailed documentation and examples!
