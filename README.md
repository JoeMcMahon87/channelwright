# ChannelWright Discord Bot

A serverless Discord bot that creates organized channel groups for tabletop RPG campaigns.

## Features

- `/begin-campaign` command to create campaign channel groups
- Automatic role creation with proper permissions
- Configurable channel templates (text, forum, voice)
- Private GM channels and public campaign channels
- Serverless AWS architecture for low cost

## Architecture

- **AWS Lambda**: Bot logic and Discord interactions
- **DynamoDB**: Campaign and configuration storage
- **Terraform**: Infrastructure as Code
- **Discord.py**: Discord API integration

## Quick Start

1. Configure your Discord bot token and application ID
2. Deploy infrastructure: `terraform apply`
3. Register Discord commands
4. Invite bot to your server with appropriate permissions

## Commands

- `/begin-campaign <name>`: Creates a new campaign with channels and roles

## Configuration

Channel templates are defined in `config/channel_templates.yaml` and can be customized per deployment.

## Deployment

See `docs/setup.md` for detailed deployment instructions.
