"""Configuration management for ChannelWright bot."""

import os
import yaml
import boto3
from typing import Dict, Any
from pathlib import Path


class Config:
    """Configuration manager for the bot."""
    
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.ssm_prefix = os.getenv('SSM_PARAMETER_PREFIX', '/channelwright/dev')
        
        # DynamoDB table names
        self.campaigns_table = os.getenv('DYNAMODB_CAMPAIGNS_TABLE', 'channelwright-campaigns-dev')
        self.config_table = os.getenv('DYNAMODB_CONFIG_TABLE', 'channelwright-config-dev')
        
        # Discord configuration
        self.discord_application_id = os.getenv('DISCORD_APPLICATION_ID')
        
        # Initialize AWS clients
        self.ssm_client = boto3.client('ssm', region_name=self.aws_region)
        self.dynamodb = boto3.resource('dynamodb', region_name=self.aws_region)
        
        # Channel templates
        self._channel_templates = None
    
    def get_discord_token(self) -> str:
        """Get Discord bot token from SSM Parameter Store."""
        try:
            response = self.ssm_client.get_parameter(
                Name=f"{self.ssm_prefix}/discord/bot_token",
                WithDecryption=True
            )
            return response['Parameter']['Value']
        except Exception as e:
            raise ValueError(f"Failed to get Discord token: {e}")
    
    def get_channel_templates(self) -> Dict[str, Any]:
        """Get channel templates from configuration."""
        if self._channel_templates is None:
            self._load_channel_templates()
        return self._channel_templates
    
    def _load_channel_templates(self):
        """Load channel templates from YAML file or DynamoDB."""
        # First try to load from local file (for development)
        config_path = Path(__file__).parent.parent / "config" / "channel_templates.yaml"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                self._channel_templates = yaml.safe_load(f)
        else:
            # Load from DynamoDB for production
            try:
                table = self.dynamodb.Table(self.config_table)
                response = table.get_item(Key={'config_key': 'channel_templates'})
                
                if 'Item' in response:
                    self._channel_templates = response['Item']['config_value']
                else:
                    # Use default template if none found
                    self._channel_templates = self._get_default_templates()
                    
            except Exception as e:
                print(f"Failed to load templates from DynamoDB: {e}")
                self._channel_templates = self._get_default_templates()
    
    def _get_default_templates(self) -> Dict[str, Any]:
        """Get default channel templates."""
        return {
            "default_template": {
                "channels": [
                    {
                        "name": "general",
                        "type": "text",
                        "private": False,
                        "description": "General discussion for the campaign"
                    },
                    {
                        "name": "character-sheets",
                        "type": "forum",
                        "private": False,
                        "description": "Share and discuss character sheets"
                    },
                    {
                        "name": "voice-chat",
                        "type": "voice",
                        "private": False,
                        "description": "Voice channel for game sessions"
                    },
                    {
                        "name": "gm-notes",
                        "type": "text",
                        "private": True,
                        "description": "Private GM planning and notes"
                    }
                ]
            }
        }


# Global config instance
config = Config()
