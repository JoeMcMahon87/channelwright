#!/bin/bash
set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Error: .env file not found. Copy .env.example to .env and configure it."
    exit 1
fi

# Validate required variables
if [ -z "$LAMBDA_FUNCTION_NAME" ] || [ -z "$AWS_REGION" ]; then
    echo "Error: LAMBDA_FUNCTION_NAME and AWS_REGION must be set in .env"
    exit 1
fi

echo "🚀 Deploying HelloBot to AWS Lambda..."

# Create deployment package
echo "📦 Creating deployment package..."
cd src

# Install dependencies for Lambda's Linux environment
pip install -r ../requirements.txt \
    --platform manylinux2014_x86_64 \
    --target . \
    --implementation cp \
    --python-version 3.11 \
    --only-binary=:all: \
    --upgrade

zip -r ../deployment.zip . -x "*.pyc" -x "__pycache__/*"
cd ..

# Check if Lambda function exists
if aws lambda get-function --function-name "$LAMBDA_FUNCTION_NAME" --region "$AWS_REGION" 2>/dev/null; then
    echo "📝 Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name "$LAMBDA_FUNCTION_NAME" \
        --zip-file fileb://deployment.zip \
        --region "$AWS_REGION"
    
    # Update environment variables
    aws lambda update-function-configuration \
        --function-name "$LAMBDA_FUNCTION_NAME" \
        --environment "Variables={DISCORD_PUBLIC_KEY=$DISCORD_PUBLIC_KEY}" \
        --region "$AWS_REGION"
else
    echo "✨ Creating new Lambda function..."
    aws lambda create-function \
        --function-name "$LAMBDA_FUNCTION_NAME" \
        --runtime python3.11 \
        --role "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/lambda-execution-role" \
        --handler bot.lambda_handler \
        --zip-file fileb://deployment.zip \
        --environment "Variables={DISCORD_PUBLIC_KEY=$DISCORD_PUBLIC_KEY}" \
        --region "$AWS_REGION"
fi

# Clean up
rm deployment.zip

echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Create an API Gateway endpoint pointing to this Lambda function"
echo "2. Set the Interactions Endpoint URL in Discord Developer Portal"
echo "3. Run: python scripts/register_commands.py"
