# Lambda Layer Architecture

## Overview

The Channelwright project uses **AWS Lambda Layers** to separate application code from dependencies, resulting in a clean, maintainable, and efficient deployment architecture.

## Architecture Benefits

### 1. **Dramatic Size Reduction**
- **Before**: 17.7 MB deployment package (code + dependencies)
- **After**: 12 KB application code + 20 MB shared layer
- **Result**: 99.9% smaller deployment packages

### 2. **Faster Deployments**
- Upload only 12 KB when code changes
- Layer cached by AWS Lambda
- Near-instant function updates

### 3. **Code Reusability**
- Single layer shared across multiple Lambda functions
- Update dependencies once, affects all functions
- Consistent dependency versions

### 4. **Better Organization**
- Clear separation of concerns
- Application code in `src/`
- Dependencies in `lambda-layer/`
- Easy to understand and maintain

### 5. **Version Control Benefits**
- Only track application code in git
- Dependencies excluded via `.gitignore`
- Smaller repository size
- Cleaner diffs

## Directory Structure

```
channelwright/
├── src/                        # 📦 Application Code (12 KB)
│   ├── bot.py                 # Main Lambda handler
│   ├── worker.py              # Worker Lambda handler
│   └── channelwright/         # Application module
│       ├── __init__.py
│       ├── bot.py            # Bot logic
│       ├── worker.py         # Worker logic
│       ├── campaign_config.py
│       └── config/           # Channel definitions
│
├── lambda-layer/               # 📚 Dependencies Layer (20 MB)
│   └── python/                # Lambda layer format
│       ├── boto3/
│       ├── requests/
│       ├── discord_interactions/
│       ├── PyNaCl/
│       └── [other packages]
│
├── config/                     # 📝 Configuration (source)
│   └── campaign_channels.yaml
│
├── scripts/
│   ├── build-layer.sh         # Build and publish layer
│   └── deploy-with-layer.sh   # Deploy with layer
│
└── infrastructure/
    └── sqs-worker.yaml        # CloudFormation template
```

## Lambda Layer Details

### Layer Name
`channelwright-dependencies`

### Layer ARN
```
arn:aws:lambda:us-east-1:296866391268:layer:channelwright-dependencies:1
```

### Compatible Runtimes
- Python 3.11

### Contents
All Python dependencies from `requirements.txt`:
- boto3 (AWS SDK)
- requests (HTTP library)
- discord-interactions (Discord API)
- PyYAML (YAML parser)
- PyNaCl (Cryptography)
- python-dotenv (Environment variables)

### Layer Structure
```
lambda-layer/
└── python/                    # Required directory name
    ├── boto3/
    ├── botocore/
    ├── requests/
    ├── discord_interactions/
    ├── nacl/
    ├── yaml/
    └── [other packages]
```

The `python/` directory is required by AWS Lambda. When the layer is attached, Lambda adds `/opt/python` to the Python path.

## Deployment Workflow

### Initial Setup (One Time)

1. **Install Dependencies**
   ```bash
   pip3 install -r requirements.txt -t lambda-layer/python/ \
       --platform manylinux2014_x86_64 \
       --only-binary=:all: \
       --python-version 311 \
       --implementation cp \
       --abi cp311
   ```

2. **Build and Publish Layer**
   ```bash
   ./scripts/build-layer.sh
   ```
   
   This creates `lambda-layer.zip` and publishes it to AWS as version 1.

### Regular Deployments

**When you modify application code:**

```bash
./scripts/deploy-with-layer.sh
```

This:
1. Packages only `src/` directory (12 KB)
2. Uploads to Lambda functions
3. Attaches the layer automatically
4. Updates both main and worker Lambdas

**When you update dependencies:**

1. Update `requirements.txt`
2. Reinstall to `lambda-layer/python/`
3. Run `./scripts/build-layer.sh` (creates version 2)
4. Run `./scripts/deploy-with-layer.sh` (uses latest version)

## How Lambda Layers Work

### Layer Path Resolution

When a Lambda function has a layer attached:

1. **Layer contents** are extracted to `/opt/`
2. **Python packages** in `/opt/python/` are added to `sys.path`
3. **Application code** in `/var/task/` can import from layer

### Import Resolution Order

```python
# In bot.py
import boto3                                    # From layer
from channelwright.campaign_config import ...   # From application
```

Python searches in this order:
1. `/var/task/` (application code)
2. `/opt/python/` (layer packages)
3. Built-in modules

### Multiple Layers

Lambda supports up to 5 layers per function. Layers are applied in order:
- Layer 1: `/opt/layer1/`
- Layer 2: `/opt/layer2/`
- etc.

## Build Scripts

### build-layer.sh

Creates and publishes the Lambda layer:

```bash
#!/bin/bash
# 1. Create lambda-layer.zip from lambda-layer/python/
# 2. Publish to AWS Lambda
# 3. Output layer ARN and version
```

**Usage:**
```bash
./scripts/build-layer.sh
```

**Output:**
- `lambda-layer.zip` (20 MB)
- Layer version number
- Layer ARN

### deploy-with-layer.sh

Deploys application code with layer attached:

```bash
#!/bin/bash
# 1. Get latest layer ARN
# 2. Package src/ directory
# 3. Update Lambda function code
# 4. Attach layer to function
# 5. Repeat for worker Lambda
```

**Usage:**
```bash
./scripts/deploy-with-layer.sh
```

**Output:**
- `deployment.zip` (12 KB)
- Updated Lambda functions
- Layer attachment confirmation

## Layer Versioning

### Version Management

Each time you publish a layer, AWS creates a new version:
- Version 1: Initial dependencies
- Version 2: Updated dependencies
- Version 3: Added new packages
- etc.

### Version Immutability

Layer versions are **immutable**:
- Cannot modify existing version
- Must publish new version for changes
- Old versions remain available

### Version Selection

The deployment script always uses the **latest version**:

```bash
LAYER_ARN=$(aws lambda list-layer-versions \
    --layer-name channelwright-dependencies \
    --query 'LayerVersions[0].LayerVersionArn' \
    --output text)
```

### Rollback Strategy

To rollback to a previous layer version:

```bash
# List all versions
aws lambda list-layer-versions \
    --layer-name channelwright-dependencies

# Attach specific version
aws lambda update-function-configuration \
    --function-name discord_channelwright_bot \
    --layers arn:aws:lambda:us-east-1:ACCOUNT:layer:channelwright-dependencies:1
```

## Dependency Management

### Adding New Dependencies

1. Add to `requirements.txt`
2. Install to layer:
   ```bash
   pip3 install -r requirements.txt -t lambda-layer/python/ \
       --platform manylinux2014_x86_64 \
       --only-binary=:all: \
       --python-version 311
   ```
3. Rebuild layer:
   ```bash
   ./scripts/build-layer.sh
   ```
4. Deploy:
   ```bash
   ./scripts/deploy-with-layer.sh
   ```

### Updating Dependencies

Same process as adding - reinstall all dependencies to ensure compatibility.

### Removing Dependencies

1. Remove from `requirements.txt`
2. Delete from `lambda-layer/python/`
3. Rebuild and redeploy

## Size Limits

### Lambda Layer Limits
- **Unzipped**: 250 MB per layer
- **Total (all layers)**: 250 MB unzipped
- **Zip file**: No explicit limit (but must fit in S3)

### Current Usage
- **Layer size**: 20 MB (unzipped: ~60 MB)
- **Application**: 12 KB
- **Total**: Well under limits

### Optimization Tips

If layer grows too large:
1. **Split into multiple layers** (e.g., AWS SDK layer, app dependencies layer)
2. **Remove unused packages**
3. **Use lighter alternatives** (e.g., `httpx` instead of `requests`)
4. **Exclude unnecessary files** (tests, docs, examples)

## Comparison: Before vs After

### Before (No Layer)

```
Deployment Package: 17.7 MB
├── bot.py
├── worker.py
├── channelwright/
├── boto3/              ← 5 MB
├── botocore/           ← 8 MB
├── requests/           ← 500 KB
└── [other deps]        ← 4 MB
```

**Problems:**
- Large upload on every change
- Slow deployments
- Mixed application and dependencies
- Hard to maintain

### After (With Layer)

```
Layer: 20 MB (shared, cached)
└── python/
    ├── boto3/
    ├── botocore/
    ├── requests/
    └── [other deps]

Deployment Package: 12 KB
├── bot.py
├── worker.py
└── channelwright/
```

**Benefits:**
- ✅ 99.9% smaller deployments
- ✅ Instant updates
- ✅ Clear separation
- ✅ Easy maintenance

## Best Practices

### 1. Layer Naming
Use descriptive names:
- `channelwright-dependencies` ✅
- `my-layer` ❌

### 2. Version Documentation
Document what changed in each version:
```
Version 1: Initial dependencies
Version 2: Added PyYAML 6.0.3
Version 3: Updated boto3 to 1.40.50
```

### 3. Testing
Test layer changes before production:
1. Publish new layer version
2. Test with dev Lambda
3. Promote to production

### 4. Cleanup
Delete old layer versions you no longer need:
```bash
aws lambda delete-layer-version \
    --layer-name channelwright-dependencies \
    --version-number 1
```

### 5. Monitoring
Monitor layer usage:
- Check Lambda function configurations
- Track layer versions in use
- Monitor deployment sizes

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'boto3'`

**Solution**: Verify layer is attached:
```bash
aws lambda get-function-configuration \
    --function-name discord_channelwright_bot \
    --query 'Layers'
```

### Version Mismatch

**Problem**: Old dependency version being used

**Solution**: Publish new layer version and update function

### Size Limits

**Problem**: Layer too large

**Solution**: Split into multiple layers or remove unused packages

## Future Enhancements

Potential improvements:

1. **Separate Layers**
   - AWS SDK layer (boto3, botocore)
   - Application dependencies layer (requests, discord-interactions)

2. **Automated Layer Updates**
   - CI/CD pipeline for layer builds
   - Automatic version bumping
   - Dependency scanning

3. **Layer Sharing**
   - Share layer across multiple projects
   - Organization-wide dependency management

4. **Layer Caching**
   - Local layer cache for development
   - Faster local testing

## Conclusion

Lambda Layers provide a clean, efficient architecture for the Channelwright project:

- **12 KB deployments** instead of 17.7 MB
- **Clear separation** of code and dependencies
- **Faster updates** and easier maintenance
- **Reusable** across multiple functions

This architecture is production-ready and follows AWS best practices for Lambda development.
