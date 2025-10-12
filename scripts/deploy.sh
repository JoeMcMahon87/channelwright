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

# Zip source code
zip -r ../deployment.zip . -x "*.pyc" -x "__pycache__/*"

# Add config directory to the zip
cd ..
zip -r deployment.zip config/
cd src
cd ..

# Check if Lambda function exists
if aws lambda get-function --function-name "$LAMBDA_FUNCTION_NAME" --region "$AWS_REGION" --query 'Configuration.FunctionName' --output text >/dev/null 2>&1; then
    echo "📝 Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name "$LAMBDA_FUNCTION_NAME" \
        --zip-file fileb://deployment.zip \
        --region "$AWS_REGION" \
        --query '{FunctionName: FunctionName, Runtime: Runtime, CodeSize: CodeSize, LastModified: LastModified}' \
        --output json
    
    echo "🔐 Updating environment variables and timeout (sensitive data hidden)..."
    # Update environment variables and timeout
    aws lambda update-function-configuration \
        --function-name "$LAMBDA_FUNCTION_NAME" \
        --environment "Variables={DISCORD_PUBLIC_KEY=$DISCORD_PUBLIC_KEY,DISCORD_BOT_TOKEN=$DISCORD_BOT_TOKEN}" \
        --timeout 30 \
        --region "$AWS_REGION" \
        --query '{FunctionName: FunctionName, Runtime: Runtime, Timeout: Timeout, LastModified: LastModified, State: State}' \
        --output json
else
    echo "✨ Creating new Lambda function..."
    echo "🔐 Setting environment variables and timeout (sensitive data hidden)..."
    aws lambda create-function \
        --function-name "$LAMBDA_FUNCTION_NAME" \
        --runtime python3.11 \
        --role "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/lambda-execution-role" \
        --handler bot.lambda_handler \
        --zip-file fileb://deployment.zip \
        --environment "Variables={DISCORD_PUBLIC_KEY=$DISCORD_PUBLIC_KEY,DISCORD_BOT_TOKEN=$DISCORD_BOT_TOKEN}" \
        --timeout 30 \
        --region "$AWS_REGION" \
        --query '{FunctionName: FunctionName, FunctionArn: FunctionArn, Runtime: Runtime, Handler: Handler, Timeout: Timeout, CodeSize: CodeSize, State: State}' \
        --output json
fi

# Clean up
rm deployment.zip

echo "✅ Deployment complete!"
echo ""

# Check for existing API Gateway and update integration
echo "🔍 Checking for API Gateway..."
API_ID=$(aws apigatewayv2 get-apis --query "Items[?Name=='hellobot-api' || Name=='channelwright-api'].ApiId" --output text --region "$AWS_REGION")

if [ -n "$API_ID" ]; then
    echo "📡 Found API Gateway: $API_ID"
    
    # Get Lambda ARN
    LAMBDA_ARN=$(aws lambda get-function --function-name "$LAMBDA_FUNCTION_NAME" --region "$AWS_REGION" --query 'Configuration.FunctionArn' --output text)
    
    # Get integration ID
    INTEGRATION_ID=$(aws apigatewayv2 get-integrations --api-id "$API_ID" --region "$AWS_REGION" --query 'Items[0].IntegrationId' --output text)
    
    if [ -n "$INTEGRATION_ID" ]; then
        echo "🔄 Updating API Gateway integration to point to new Lambda function..."
        aws apigatewayv2 update-integration \
            --api-id "$API_ID" \
            --integration-id "$INTEGRATION_ID" \
            --integration-uri "$LAMBDA_ARN" \
            --region "$AWS_REGION" > /dev/null 2>&1
        
        # Grant API Gateway permission to invoke Lambda
        aws lambda add-permission \
            --function-name "$LAMBDA_FUNCTION_NAME" \
            --statement-id apigateway-invoke-$(date +%s) \
            --action lambda:InvokeFunction \
            --principal apigatewayv2.amazonaws.com \
            --source-arn "arn:aws:execute-api:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):$API_ID/*/*" \
            --region "$AWS_REGION" > /dev/null 2>&1 || true
    fi
    
    # Get API endpoint
    API_ENDPOINT=$(aws apigatewayv2 get-api --api-id "$API_ID" --region "$AWS_REGION" --query 'ApiEndpoint' --output text)
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎉 Discord Interactions Endpoint URL:"
    echo ""
    echo "   $API_ENDPOINT"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📋 Next steps:"
    echo "1. Go to Discord Developer Portal"
    echo "2. Navigate to your application → General Information"
    echo "3. Set 'Interactions Endpoint URL' to: $API_ENDPOINT"
    echo "4. Run: python3 scripts/register_commands.py"
else
    echo "⚠️  No API Gateway found. Creating one..."
    
    # Get Lambda ARN
    LAMBDA_ARN=$(aws lambda get-function --function-name "$LAMBDA_FUNCTION_NAME" --region "$AWS_REGION" --query 'Configuration.FunctionArn' --output text)
    
    # Create API Gateway
    API_ID=$(aws apigatewayv2 create-api \
        --name channelwright-api \
        --protocol-type HTTP \
        --target "$LAMBDA_ARN" \
        --region "$AWS_REGION" \
        --query 'ApiId' \
        --output text)
    
    # Grant API Gateway permission to invoke Lambda
    aws lambda add-permission \
        --function-name "$LAMBDA_FUNCTION_NAME" \
        --statement-id apigateway-invoke-$(date +%s) \
        --action lambda:InvokeFunction \
        --principal apigatewayv2.amazonaws.com \
        --source-arn "arn:aws:execute-api:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):$API_ID/*/*" \
        --region "$AWS_REGION" > /dev/null 2>&1
    
    # Get API endpoint
    API_ENDPOINT=$(aws apigatewayv2 get-api --api-id "$API_ID" --region "$AWS_REGION" --query 'ApiEndpoint' --output text)
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎉 Discord Interactions Endpoint URL:"
    echo ""
    echo "   $API_ENDPOINT"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📋 Next steps:"
    echo "1. Go to Discord Developer Portal"
    echo "2. Navigate to your application → General Information"
    echo "3. Set 'Interactions Endpoint URL' to: $API_ENDPOINT"
    echo "4. Run: python3 scripts/register_commands.py"
fi
