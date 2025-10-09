"""Database operations for ChannelWright bot."""

import boto3
from typing import Optional, List, Dict, Any
from datetime import datetime
from botocore.exceptions import ClientError

from config import config
from models import Campaign, BotConfig


class DatabaseManager:
    """Manages DynamoDB operations for the bot."""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name=config.aws_region)
        self.campaigns_table = self.dynamodb.Table(config.campaigns_table)
        self.config_table = self.dynamodb.Table(config.config_table)
    
    async def save_campaign(self, campaign: Campaign) -> bool:
        """Save a campaign to DynamoDB."""
        try:
            item = campaign.dict()
            self.campaigns_table.put_item(Item=item)
            return True
        except ClientError as e:
            print(f"Error saving campaign: {e}")
            return False
    
    async def get_campaign(self, guild_id: str, campaign_name: str) -> Optional[Campaign]:
        """Get a campaign from DynamoDB."""
        try:
            response = self.campaigns_table.get_item(
                Key={
                    'guild_id': guild_id,
                    'campaign_name': campaign_name
                }
            )
            
            if 'Item' in response:
                return Campaign(**response['Item'])
            return None
            
        except ClientError as e:
            print(f"Error getting campaign: {e}")
            return None
    
    async def list_campaigns(self, guild_id: str) -> List[Campaign]:
        """List all campaigns for a guild."""
        try:
            response = self.campaigns_table.query(
                KeyConditionExpression='guild_id = :guild_id',
                ExpressionAttributeValues={':guild_id': guild_id}
            )
            
            campaigns = []
            for item in response.get('Items', []):
                campaigns.append(Campaign(**item))
            
            return campaigns
            
        except ClientError as e:
            print(f"Error listing campaigns: {e}")
            return []
    
    async def delete_campaign(self, guild_id: str, campaign_name: str) -> bool:
        """Delete a campaign from DynamoDB."""
        try:
            self.campaigns_table.delete_item(
                Key={
                    'guild_id': guild_id,
                    'campaign_name': campaign_name
                }
            )
            return True
            
        except ClientError as e:
            print(f"Error deleting campaign: {e}")
            return False
    
    async def campaign_exists(self, guild_id: str, campaign_name: str) -> bool:
        """Check if a campaign already exists."""
        campaign = await self.get_campaign(guild_id, campaign_name)
        return campaign is not None
    
    async def save_config(self, config_key: str, config_value: Dict[str, Any]) -> bool:
        """Save configuration to DynamoDB."""
        try:
            bot_config = BotConfig(
                config_key=config_key,
                config_value=config_value
            )
            
            self.config_table.put_item(Item=bot_config.dict())
            return True
            
        except ClientError as e:
            print(f"Error saving config: {e}")
            return False
    
    async def get_config(self, config_key: str) -> Optional[Dict[str, Any]]:
        """Get configuration from DynamoDB."""
        try:
            response = self.config_table.get_item(
                Key={'config_key': config_key}
            )
            
            if 'Item' in response:
                return response['Item']['config_value']
            return None
            
        except ClientError as e:
            print(f"Error getting config: {e}")
            return None


# Global database manager instance
db = DatabaseManager()
