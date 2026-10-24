#!/bin/bash
set -e

echo "🏗️  Building Lambda Layer"
echo "========================================"

# Clean up old layer package and dependencies
rm -f lambda-layer.zip
rm -rf lambda-layer/python

# Install packages for Lambda compatibility (manylinux2014)
echo "Installing packages for Lambda runtime (Python 3.13, manylinux2014)..."
pip3 install -r requirements.txt -t lambda-layer/python/ \
    --platform manylinux2014_x86_64 \
    --only-binary=:all: \
    --python-version 313 \
    --implementation cp \
    --abi cp313

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
    --compatible-runtimes python3.13 \
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
