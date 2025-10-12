# Changelog

## [Unreleased] - 2025-10-11

### Added
- `/add-campaign` command now creates both a channel category and a role
- Role is automatically named "[Campaign Name] Members"
- Comprehensive logging throughout the bot for debugging
- Security improvements to hide sensitive environment variables in deployment output
- API Gateway permission management in deployment script

### Changed
- Updated deployment script to suppress environment variables from AWS CLI output
- Enhanced error handling with full tracebacks in logs
- Improved command response messages to show both category and role creation

### Features

#### `/hellobot`
- Simple greeting command
- Responds with personalized message using username

#### `/add-campaign <name>`
- Creates a Discord channel category with the specified name
- Creates a role named "[Campaign Name] Members"
- Role is mentionable but has no special permissions
- Provides clear success/error messages

### Required Permissions
- `applications.commands` - For slash commands
- `Send Messages` - For bot responses
- `Manage Channels` - For creating categories
- `Manage Roles` - For creating roles

### Deployment
- Serverless architecture using AWS Lambda
- API Gateway for Discord webhook endpoint
- Secure environment variable handling
- Comprehensive CloudWatch logging

### Next Steps
- Add ability to assign users to campaign roles
- Create default channels within campaign categories
- Add campaign management commands (list, delete, etc.)
- Store campaign metadata in DynamoDB
