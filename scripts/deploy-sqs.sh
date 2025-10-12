#!/bin/bash
set -e

echo "🚀 Deploying Channelwright with SQS Architecture"
echo "================================================"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Error: .env file not found. Copy .env.example to .env and configure it."
    exit 1
fi

# Validate required variables
if [ -z "$LAMBDA_FUNCTION_NAME" ] || [ -z "$AWS_REGION" ] || [ -z "$DISCORD_BOT_TOKEN" ]; then
    echo "Error: Required environment variables not set in .env"
    exit 1
fi

echo "📦 Step 1: Creating deployment package..."

# Copy config to channelwright module
echo "Copying config directory to channelwright module..."
cp -r config src/channelwright/

# Clean up any existing packages
echo "Cleaning up old packages..."
cd src
find . -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
rm -rf nacl/ cffi/ pycparser/ _cffi_backend*.so boto* dateutil/ jmespath* s3transfer* six* urllib3* certifi* charset_normalizer* idna* requests* yaml* discord_interactions* python_dotenv* 2>/dev/null || true

# Install packages for Lambda compatibility (manylinux2014)
echo "Installing packages for Lambda runtime (Python 3.11, manylinux2014)..."
pip3 install -r ../requirements.txt -t . \
    --platform manylinux2014_x86_64 \
    --only-binary=:all: \
    --python-version 311 \
    --implementation cp \
    --abi cp311 \
    --upgrade

# Create deployment package
echo "Creating deployment package..."
zip -r ../deployment.zip . -x "*.pyc" -x "__pycache__/*" -x "channelwright/__pycache__/*"
cd ..

echo ""
echo "🔧 Step 2: Creating/Updating SQS Queue and Worker Lambda..."

# Check if stack exists
STACK_NAME="channelwright-sqs-stack"
if aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION >/dev/null 2>&1; then
    echo "Updating existing CloudFormation stack..."
    aws cloudformation update-stack \
        --stack-name $STACK_NAME \
        --template-body file://infrastructure/sqs-worker.yaml \
        --parameters \
            ParameterKey=DiscordBotToken,ParameterValue=$DISCORD_BOT_TOKEN \
            ParameterKey=MainLambdaArn,ParameterValue=arn:aws:lambda:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):function:$LAMBDA_FUNCTION_NAME \
        --capabilities CAPABILITY_NAMED_IAM \
        --region $AWS_REGION
    
    echo "Waiting for stack update to complete..."
    aws cloudformation wait stack-update-complete --stack-name $STACK_NAME --region $AWS_REGION
else
    echo "Creating new CloudFormation stack..."
    aws cloudformation create-stack \
        --stack-name $STACK_NAME \
        --template-body file://infrastructure/sqs-worker.yaml \
        --parameters \
            ParameterKey=DiscordBotToken,ParameterValue=$DISCORD_BOT_TOKEN \
            ParameterKey=MainLambdaArn,ParameterValue=arn:aws:lambda:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):function:$LAMBDA_FUNCTION_NAME \
        --capabilities CAPABILITY_NAMED_IAM \
        --region $AWS_REGION
    
    echo "Waiting for stack creation to complete..."
    aws cloudformation wait stack-create-complete --stack-name $STACK_NAME --region $AWS_REGION
fi

# Get Queue URL from stack outputs
QUEUE_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`QueueUrl`].OutputValue' \
    --output text)

echo "✅ Queue URL: $QUEUE_URL"

# Get Queue ARN
QUEUE_ARN=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`QueueArn`].OutputValue' \
    --output text)

echo "✅ Queue ARN: $QUEUE_ARN"

echo ""
echo "🔐 Adding SQS permissions to main Lambda role..."

# Add SQS policy to main Lambda role
aws iam put-role-policy \
    --role-name lambda-execution-role \
    --policy-name ChannelwrightSQSPolicy \
    --policy-document "{
        \"Version\": \"2012-10-17\",
        \"Statement\": [
            {
                \"Effect\": \"Allow\",
                \"Action\": [
                    \"sqs:SendMessage\",
                    \"sqs:GetQueueUrl\"
                ],
                \"Resource\": \"$QUEUE_ARN\"
            }
        ]
    }"

echo "✅ SQS permissions added"

echo ""
echo "📝 Step 3: Updating main Lambda function..."

# Update main Lambda code
aws lambda update-function-code \
    --function-name $LAMBDA_FUNCTION_NAME \
    --zip-file fileb://deployment.zip \
    --region $AWS_REGION \
    --query '{FunctionName: FunctionName, Runtime: Runtime, CodeSize: CodeSize}' \
    --output json

# Update main Lambda environment variables
aws lambda update-function-configuration \
    --function-name $LAMBDA_FUNCTION_NAME \
    --environment "Variables={DISCORD_PUBLIC_KEY=$DISCORD_PUBLIC_KEY,DISCORD_BOT_TOKEN=$DISCORD_BOT_TOKEN,SQS_QUEUE_URL=$QUEUE_URL}" \
    --timeout 30 \
    --region $AWS_REGION \
    --query '{FunctionName: FunctionName, Timeout: Timeout}' \
    --output json

echo ""
echo "📝 Step 4: Updating worker Lambda function..."

# Update worker Lambda code
aws lambda update-function-code \
    --function-name discord_channelwright_worker \
    --zip-file fileb://deployment.zip \
    --region $AWS_REGION \
    --query '{FunctionName: FunctionName, Runtime: Runtime, CodeSize: CodeSize}' \
    --output json

# Clean up
rm deployment.zip

echo ""
echo "✅ Deployment complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Architecture Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Main Lambda: $LAMBDA_FUNCTION_NAME"
echo "  - Receives Discord interactions"
echo "  - Creates role & category"
echo "  - Queues channel creation tasks"
echo "  - Returns deferred response (type 5)"
echo ""
echo "SQS Queue: $QUEUE_URL"
echo "  - Stores channel creation tasks"
echo "  - Processes tasks asynchronously"
echo ""
echo "Worker Lambda: discord_channelwright_worker"
echo "  - Triggered by SQS messages"
echo "  - Creates channels one by one"
echo "  - Updates progress via Discord webhook"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
