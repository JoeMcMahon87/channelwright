#!/bin/bash

# Deployment script for ChannelWright Discord bot
set -e

# Configuration
ENVIRONMENT=${1:-dev}
AWS_REGION=${AWS_REGION:-us-east-1}

echo "🚀 Deploying ChannelWright to environment: $ENVIRONMENT"

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is not installed. Please install Terraform first."
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install AWS CLI first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

# Check for required environment variables
if [ -z "$DISCORD_BOT_TOKEN" ]; then
    echo "❌ DISCORD_BOT_TOKEN environment variable is required."
    echo "   Please set it with: export DISCORD_BOT_TOKEN=your_token_here"
    exit 1
fi

if [ -z "$DISCORD_APPLICATION_ID" ]; then
    echo "❌ DISCORD_APPLICATION_ID environment variable is required."
    echo "   Please set it with: export DISCORD_APPLICATION_ID=your_app_id_here"
    exit 1
fi

# Build the deployment package
echo "🔨 Building deployment package..."
./scripts/build.sh

# Deploy with Terraform
echo "🏗️  Deploying infrastructure..."
cd terraform

# Initialize Terraform
terraform init

# Plan the deployment
echo "📋 Planning deployment..."
terraform plan \
    -var="environment=$ENVIRONMENT" \
    -var="discord_bot_token=$DISCORD_BOT_TOKEN" \
    -var="discord_application_id=$DISCORD_APPLICATION_ID" \
    -var="aws_region=$AWS_REGION" \
    -out=tfplan

# Apply the deployment
echo "🚀 Applying deployment..."
terraform apply tfplan

# Get outputs
echo "📊 Deployment outputs:"
LAMBDA_URL=$(terraform output -raw lambda_function_url)
LAMBDA_NAME=$(terraform output -raw lambda_function_name)

echo "✅ Deployment complete!"
echo ""
echo "📋 Deployment Summary:"
echo "   Environment: $ENVIRONMENT"
echo "   Region: $AWS_REGION"
echo "   Lambda Function: $LAMBDA_NAME"
echo "   Webhook URL: $LAMBDA_URL"
echo ""
echo "🔗 Next Steps:"
echo "   1. Configure Discord webhook URL: $LAMBDA_URL"
echo "   2. Invite bot to your Discord server"
echo "   3. Test the /begin-campaign command"
echo ""
echo "📚 For more information, see docs/setup.md"

cd - > /dev/null
