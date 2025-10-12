# Project Structure

## Overview

The Channelwright project is organized to separate application code from third-party dependencies, making it easier to maintain and understand.

## Directory Structure

```
channelwright/
├── config/                          # Configuration files (source)
│   └── campaign_channels.yaml       # Channel definitions
│
├── infrastructure/                  # AWS infrastructure templates
│   └── sqs-worker.yaml             # CloudFormation template for SQS
│
├── scripts/                         # Deployment and utility scripts
│   ├── deploy-sqs.sh               # Main deployment script
│   └── register_commands.py        # Discord command registration
│
├── src/                            # Lambda deployment package
│   ├── bot.py                      # Main Lambda handler (imports from channelwright)
│   ├── worker.py                   # Worker Lambda handler (imports from channelwright)
│   │
│   ├── channelwright/              # Application source code
│   │   ├── __init__.py            # Package initialization
│   │   ├── bot.py                 # Bot logic and interaction handling
│   │   ├── worker.py              # SQS worker logic
│   │   ├── campaign_config.py     # Configuration loader
│   │   └── config/                # Config (copied during deployment)
│   │       └── campaign_channels.yaml
│   │
│   └── [dependencies]/             # Third-party packages (boto3, requests, etc.)
│       ├── boto3/
│       ├── requests/
│       ├── discord_interactions/
│       └── ...
│
├── .env                            # Environment variables (not in git)
├── .env.example                    # Environment template
├── requirements.txt                # Python dependencies
└── README.md                       # Project documentation
```

## Key Components

### Application Code (`src/channelwright/`)

This directory contains all the custom application code:

- **`bot.py`** - Main Discord bot handler
  - Handles Discord interactions
  - Creates roles and categories
  - Queues channel creation tasks to SQS
  
- **`worker.py`** - SQS worker Lambda
  - Processes channel creation tasks
  - Updates progress via Discord webhooks
  - Handles completion notifications

- **`campaign_config.py`** - Configuration management
  - Loads YAML configuration
  - Converts to Discord API format
  - Provides helper functions

### Lambda Handlers (`src/`)

Thin wrapper files that Lambda invokes:

- **`bot.py`** - Imports and exports `lambda_handler` from `channelwright.bot`
- **`worker.py`** - Imports and exports `lambda_handler` from `channelwright.worker`

This allows Lambda to find the handler at the root level while keeping code organized.

### Dependencies (`src/[packages]/`)

Third-party Python packages installed via pip:
- Installed with `--platform manylinux2014_x86_64` for Lambda compatibility
- Includes: boto3, requests, discord-interactions, PyYAML, PyNaCl, etc.

## Deployment Process

### 1. Clean Up Old Packages
```bash
cd src
rm -rf boto3/ requests/ nacl/ # etc.
```

### 2. Copy Configuration
```bash
cp -r config src/channelwright/
```

### 3. Install Dependencies
```bash
pip3 install -r requirements.txt -t src/ \
    --platform manylinux2014_x86_64 \
    --only-binary=:all: \
    --python-version 311
```

### 4. Create Deployment Package
```bash
cd src
zip -r ../deployment.zip . \
    -x "*.pyc" \
    -x "__pycache__/*" \
    -x "channelwright/__pycache__/*"
```

### 5. Deploy to Lambda
```bash
aws lambda update-function-code \
    --function-name discord_channelwright_bot \
    --zip-file fileb://deployment.zip
```

## Benefits of This Structure

### 1. **Clear Separation**
- Application code in `channelwright/`
- Dependencies at root of `src/`
- Easy to identify what's custom vs. third-party

### 2. **Maintainability**
- All application files in one directory
- Easy to navigate and modify
- Clear import paths (`from channelwright.module import ...`)

### 3. **Lambda Compatibility**
- Handler files at root level (Lambda requirement)
- Dependencies at root for Python import system
- Application code in package for organization

### 4. **Version Control**
- Only track application code and config
- Dependencies excluded via `.gitignore`
- Reproducible via `requirements.txt`

### 5. **Testing**
- Can import `channelwright` package for testing
- Easy to mock dependencies
- Clear module boundaries

## Import Patterns

### Within Application Code
```python
# In channelwright/bot.py
from channelwright.campaign_config import DEFAULT_CAMPAIGN_CHANNELS
```

### Lambda Handlers
```python
# In src/bot.py (root level)
from channelwright.bot import lambda_handler
```

### Third-Party Dependencies
```python
# Available at root level
import boto3
import requests
from discord_interactions import verify_key
```

## Configuration Management

Configuration files are managed separately:

1. **Source**: `config/campaign_channels.yaml` (tracked in git)
2. **Deployment**: Copied to `src/channelwright/config/` during build
3. **Runtime**: Loaded by `campaign_config.py` from package directory

This ensures:
- Single source of truth in `config/`
- Configuration bundled with code in deployment
- Easy to modify without touching code

## Development Workflow

### 1. Modify Application Code
Edit files in `src/channelwright/`

### 2. Update Configuration
Edit `config/campaign_channels.yaml`

### 3. Test Locally
```bash
cd src
python -c "from channelwright.bot import lambda_handler; print('OK')"
```

### 4. Deploy
```bash
./scripts/deploy-sqs.sh
```

## Troubleshooting

### Import Errors
- Ensure handler files (`src/bot.py`, `src/worker.py`) exist at root
- Check import paths use `channelwright.` prefix
- Verify `__init__.py` exists in `channelwright/`

### Missing Dependencies
- Re-run pip install with correct platform flags
- Check `requirements.txt` is up to date
- Verify manylinux2014 wheels are used

### Configuration Not Found
- Ensure config is copied to `src/channelwright/config/`
- Check `campaign_config.py` path logic
- Verify YAML file is in deployment package

## Future Enhancements

Potential improvements to structure:

1. **Tests Directory**: Add `tests/` for unit and integration tests
2. **Shared Utilities**: Create `channelwright/utils/` for common functions
3. **Type Hints**: Add type annotations for better IDE support
4. **Documentation**: Generate API docs from docstrings
5. **Local Development**: Add Docker compose for local testing
