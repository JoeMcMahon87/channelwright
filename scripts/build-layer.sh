#!/bin/bash
set -e

echo "🏗️  Building Lambda Layer"
echo "========================================"

# Clean up old layer package
rm -f lambda-layer.zip

# Create layer package
echo "📦 Creating layer package..."
cd lambda-layer
zip -q -r ../lambda-layer.zip python/
cd ..

LAYER_SIZE=$(du -h lambda-layer.zip | cut -f1)
echo "✅ Layer package created: $LAYER_SIZE"

# Publish layer to AWS
echo ""
echo "📤 Publishing layer to AWS..."

LAYER_VERSION=$(aws lambda publish-layer-version \
    --layer-name channelwright-dependencies \
    --description "Python dependencies for Channelwright bot" \
    --zip-file fileb://lambda-layer.zip \
    --compatible-runtimes python3.11 \
    --region us-east-1 \
    --query 'Version' \
    --output text)

echo "✅ Layer published: Version $LAYER_VERSION"

# Get Layer ARN
LAYER_ARN=$(aws lambda list-layer-versions \
    --layer-name channelwright-dependencies \
    --region us-east-1 \
    --query 'LayerVersions[0].LayerVersionArn' \
    --output text)

echo ""
echo "📋 Layer Details:"
echo "   Name: channelwright-dependencies"
echo "   Version: $LAYER_VERSION"
echo "   ARN: $LAYER_ARN"
echo ""
echo "💡 Use this ARN when updating Lambda functions"
