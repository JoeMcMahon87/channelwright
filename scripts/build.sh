#!/bin/bash

# Build script for ChannelWright Discord bot
set -e

echo "🔨 Building ChannelWright Discord Bot..."

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "📁 Project root: $PROJECT_ROOT"

# Create dist directory
mkdir -p "$PROJECT_ROOT/dist"

# Create a temporary directory for the build
BUILD_DIR=$(mktemp -d)
echo "📁 Using build directory: $BUILD_DIR"

# Copy source files
echo "📋 Copying source files..."
cp -r "$PROJECT_ROOT/src"/* "$BUILD_DIR/"
cp "$PROJECT_ROOT/requirements.txt" "$BUILD_DIR/"

# Install dependencies
echo "📦 Installing dependencies..."
cd "$BUILD_DIR"
pip install -r requirements.txt -t .

# Remove unnecessary files
echo "🧹 Cleaning up..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true

# Create the deployment package
echo "📦 Creating deployment package..."
zip -r channelwright.zip . -x "*.git*" "*.DS_Store*" "*.pyc" "*__pycache__*"

# Move the package to the dist directory
echo "📦 Moving package to dist directory..."
mv "$BUILD_DIR/channelwright.zip" "$PROJECT_ROOT/dist/channelwright.zip"

# Clean up
rm -rf "$BUILD_DIR"

echo "✅ Build complete! Package created at $PROJECT_ROOT/dist/channelwright.zip"
echo "📊 Package size: $(du -h "$PROJECT_ROOT/dist/channelwright.zip" | cut -f1)"
