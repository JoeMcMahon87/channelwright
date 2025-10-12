#!/bin/bash
set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "🚀 Deploying Channelwright Bot with Lambda Layer"
echo "========================================"

# Validate required variables
if [ -z "$LAMBDA_FUNCTION_NAME" ] || [ -z "$AWS_REGION" ] || [ -z "$DISCORD_BOT_TOKEN" ]; then
    echo "Error: Required environment variables not set in .env"
    exit 1
fi

# Get the latest layer ARN
echo "📋 Getting Lambda Layer ARN..."
LAYER_ARN=$(aws lambda list-layer-versions \
    --layer-name channelwright-dependencies \
    --region $AWS_REGION \
    --query 'LayerVersions[0].LayerVersionArn' \
    --output text 2>/dev/null || echo "")

if [ -z "$LAYER_ARN" ]; then
    echo "❌ Lambda Layer not found. Please run ./scripts/build-layer.sh first"
    exit 1
fi

echo "✅ Using Layer: $LAYER_ARN"

echo ""
echo "📦 Step 1: Creating deployment package..."

# Copy config to channelwright module
echo "Copying config directory to channelwright module..."
cp -r config src/channelwright/

# Create deployment package (only application code)
echo "Creating deployment package..."
cd src
rm -f ../deployment.zip
zip -q -r ../deployment.zip . -x "*.pyc" -x "__pycache__/*" -x "channelwright/__pycache__/*"
cd ..

PACKAGE_SIZE=$(du -h deployment.zip | cut -f1)
echo "✅ Package created: $PACKAGE_SIZE (application code only)"

echo ""
echo "📤 Step 2: Deploying Lambda functions..."

# Update main Lambda
echo "Updating main Lambda function..."
aws lambda update-function-code \
    --function-name $LAMBDA_FUNCTION_NAME \
    --zip-file fileb://deployment.zip \
    --region $AWS_REGION \
    --query '{FunctionName:FunctionName,CodeSize:CodeSize}' \
    --output json

# Wait for update to complete
echo "Waiting for main Lambda update..."
aws lambda wait function-updated \
    --function-name $LAMBDA_FUNCTION_NAME \
    --region $AWS_REGION

# Update main Lambda layer
echo "Attaching layer to main Lambda..."
aws lambda update-function-configuration \
    --function-name $LAMBDA_FUNCTION_NAME \
    --layers $LAYER_ARN \
    --region $AWS_REGION \
    --query '{FunctionName:FunctionName,Layers:Layers[*].Arn}' \
    --output json

# Update worker Lambda
echo ""
echo "Updating worker Lambda function..."
aws lambda update-function-code \
    --function-name discord_channelwright_worker \
    --zip-file fileb://deployment.zip \
    --region $AWS_REGION \
    --query '{FunctionName:FunctionName,CodeSize:CodeSize}' \
    --output json

# Wait for update to complete
echo "Waiting for worker Lambda update..."
aws lambda wait function-updated \
    --function-name discord_channelwright_worker \
    --region $AWS_REGION

# Update worker Lambda layer
echo "Attaching layer to worker Lambda..."
aws lambda update-function-configuration \
    --function-name discord_channelwright_worker \
    --layers $LAYER_ARN \
    --region $AWS_REGION \
    --query '{FunctionName:FunctionName,Layers:Layers[*].Arn}' \
    --output json

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "📊 Summary:"
echo "   Application Package: $PACKAGE_SIZE"
echo "   Lambda Layer: $LAYER_ARN"
echo "   Main Lambda: $LAMBDA_FUNCTION_NAME"
echo "   Worker Lambda: discord_channelwright_worker"
echo ""
echo "🎉 Bot is ready to use!"
