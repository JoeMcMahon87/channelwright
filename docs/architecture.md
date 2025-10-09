# ChannelWright Architecture

This document describes the technical architecture of the ChannelWright Discord bot.

## Overview

ChannelWright is a serverless Discord bot built on AWS that helps create organized channel structures for tabletop RPG campaigns. The architecture follows AWS best practices for serverless applications with a focus on cost optimization and scalability.

## Architecture Diagram

```
Discord API
    ↓ (Webhook)
AWS Lambda Function URL
    ↓
Lambda Function (Python 3.11)
    ↓
DynamoDB Tables
    ↓
Systems Manager Parameter Store
```

## Components

### 1. Discord Integration

- **Discord Bot Application**: Registered with Discord Developer Portal
- **Slash Commands**: `/begin-campaign` and `/list-campaigns`
- **Webhook Endpoint**: AWS Lambda Function URL receives Discord interactions
- **Permissions**: Bot requires Manage Channels, Manage Roles, and View Channels

### 2. AWS Lambda Function

- **Runtime**: Python 3.11
- **Memory**: 256 MB (configurable)
- **Timeout**: 30 seconds (configurable)
- **Trigger**: Lambda Function URL (no API Gateway needed)
- **Libraries**: discord.py, boto3, pydantic

#### Function Structure:
```
src/
├── lambda_function.py      # Main Lambda handler
├── discord_bot.py         # Discord bot implementation
├── config.py             # Configuration management
├── database.py           # DynamoDB operations
└── models.py            # Data models
```

### 3. Data Storage

#### DynamoDB Tables:

**Campaigns Table** (`channelwright-campaigns-{env}`)
- **Partition Key**: `guild_id` (Discord server ID)
- **Sort Key**: `campaign_name`
- **Attributes**: category_id, role_id, channels, created_by, created_at, template_used
- **GSI**: CreatedAtIndex for querying by creation date

**Configuration Table** (`channelwright-config-{env}`)
- **Partition Key**: `config_key`
- **Attributes**: config_value, updated_at
- **Purpose**: Store channel templates and bot configuration

### 4. Security

#### AWS Systems Manager Parameter Store:
- **Bot Token**: Stored as SecureString parameter
- **Application ID**: Stored as String parameter
- **Path**: `/{project_name}/{environment}/discord/`

#### IAM Permissions:
- **Lambda Execution Role**: Basic execution permissions
- **DynamoDB Access**: Read/write to both tables
- **SSM Access**: Read parameters for Discord credentials

### 5. Infrastructure as Code

**Terraform Configuration**:
- `main.tf` - Provider and data sources
- `variables.tf` - Input variables
- `dynamodb.tf` - DynamoDB tables
- `iam.tf` - IAM roles and policies
- `lambda.tf` - Lambda function and CloudWatch logs
- `ssm.tf` - Parameter Store configuration
- `outputs.tf` - Deployment outputs

## Data Flow

### Campaign Creation Flow:

1. **User Input**: User runs `/begin-campaign name:Campaign Name`
2. **Discord Webhook**: Discord sends interaction to Lambda Function URL
3. **Authentication**: Lambda retrieves bot token from Parameter Store
4. **Validation**: Check if campaign name already exists in DynamoDB
5. **Discord Operations**:
   - Create category channel
   - Create member role
   - Create channels based on template
   - Set permissions
6. **Data Persistence**: Save campaign data to DynamoDB
7. **Response**: Send success embed to Discord

### Channel Template System:

1. **Template Loading**: Load from `channel_templates.yaml` or DynamoDB
2. **Template Processing**: Parse channel definitions (name, type, private flag)
3. **Channel Creation**: Create channels based on template
4. **Permission Setup**: Apply role-based permissions

## Scalability Considerations

### Cost Optimization:
- **Serverless Architecture**: Pay only for actual usage
- **DynamoDB On-Demand**: No provisioned capacity needed
- **Lambda Function URL**: No API Gateway costs
- **CloudWatch Logs**: 14-day retention to minimize storage costs

### Performance:
- **Cold Start Mitigation**: Lightweight dependencies and optimized imports
- **Concurrent Execution**: Lambda can handle multiple simultaneous requests
- **Database Performance**: DynamoDB provides consistent single-digit millisecond latency

### Limits:
- **Lambda Timeout**: 30 seconds (sufficient for Discord operations)
- **Discord Rate Limits**: Built-in handling in discord.py library
- **DynamoDB Limits**: 400 KB item size limit (adequate for campaign data)

## Security Model

### Authentication:
- **Discord Signature Verification**: Validates requests from Discord (simplified in current implementation)
- **AWS IAM**: Principle of least privilege for Lambda execution role
- **Parameter Store**: Encrypted storage for sensitive configuration

### Authorization:
- **Discord Permissions**: Bot requires specific permissions in each server
- **Role Hierarchy**: Bot role must be above created campaign roles
- **Channel Permissions**: Private channels restricted to guild owner and GM role

### Data Protection:
- **Encryption at Rest**: DynamoDB and Parameter Store use AWS KMS
- **Encryption in Transit**: HTTPS for all API communications
- **No Sensitive Data Logging**: Bot tokens and user data not logged

## Monitoring and Observability

### CloudWatch Integration:
- **Lambda Logs**: Function execution logs with 14-day retention
- **Metrics**: Lambda duration, error rate, invocation count
- **Alarms**: Can be configured for error rates or execution failures

### Error Handling:
- **Graceful Degradation**: Bot continues operating if non-critical operations fail
- **User Feedback**: Clear error messages sent to Discord users
- **Logging**: Detailed error logging for debugging

## Deployment Strategy

### Environment Separation:
- **Development**: `channelwright-*-dev` resources
- **Production**: `channelwright-*-prod` resources
- **Terraform State**: Separate state files per environment

### CI/CD Pipeline:
1. **Build**: Package Lambda function with dependencies
2. **Test**: Run unit tests (future enhancement)
3. **Deploy**: Terraform apply with environment-specific variables
4. **Verify**: Register commands and test basic functionality

## Future Enhancements

### Planned Features:
- **Campaign Management**: Edit/delete campaigns
- **Custom Templates**: Per-server template customization
- **Role Management**: Automatic role assignment
- **Audit Logging**: Track all bot operations

### Technical Improvements:
- **Discord Signature Verification**: Full implementation
- **Error Recovery**: Retry mechanisms for failed operations
- **Performance Monitoring**: Custom CloudWatch metrics
- **Automated Testing**: Unit and integration tests

## Configuration Management

### Channel Templates:
Templates define the structure of channels created for each campaign:

```yaml
default_template:
  channels:
    - name: "general"
      type: "text"
      private: false
      description: "General discussion"
    - name: "gm-notes"
      type: "text"
      private: true
      description: "GM planning space"
```

### Environment Variables:
- `ENVIRONMENT`: Deployment environment
- `DYNAMODB_CAMPAIGNS_TABLE`: Campaigns table name
- `DYNAMODB_CONFIG_TABLE`: Configuration table name
- `DISCORD_APPLICATION_ID`: Discord application ID
- `SSM_PARAMETER_PREFIX`: Parameter Store path prefix

This architecture provides a robust, scalable, and cost-effective solution for Discord bot operations while maintaining security and operational best practices.
