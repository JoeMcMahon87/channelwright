"""
Campaign Configuration Loader
Loads channel configuration from YAML file
"""
import os
import yaml


def get_channel_type_name(channel_type):
    """
    Convert Discord channel type number to human-readable name
    """
    type_map = {
        0: 'Text',
        2: 'Voice',
        15: 'Forum'
    }
    return type_map.get(channel_type, 'Unknown')

def load_campaign_channels():
    """
    Load campaign channel configuration from YAML file
    Returns list of channel configurations
    """
    # Try to load from config directory
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'campaign_channels.yaml')
    
    # For Lambda, config is in the deployment package
    if not os.path.exists(config_path):
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'campaign_channels.yaml')
    
    # If still not found, try relative to current directory
    if not os.path.exists(config_path):
        config_path = 'config/campaign_channels.yaml'
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            channels = config.get('channels', [])
            
            # Convert YAML format to Discord API format
            discord_channels = []
            for channel in channels:
                channel_type = 0  # Default to text
                if channel.get('type') == 'voice':
                    channel_type = 2
                elif channel.get('type') == 'forum':
                    channel_type = 15
                
                discord_channels.append({
                    'name': channel['name'],
                    'type': channel_type,
                    'gm_only': channel.get('gm_only', False)
                })
            
            return discord_channels
    except Exception as e:
        print(f"Error loading campaign config: {e}")
        # Return default fallback configuration
        return [
            {'name': 'general', 'type': 0, 'gm_only': False},
            {'name': 'session-notes', 'type': 0, 'gm_only': False},
            {'name': 'gm-notes', 'type': 0, 'gm_only': True},
            {'name': 'voice-chat', 'type': 2, 'gm_only': False},
            {'name': 'character-sheets', 'type': 15, 'gm_only': False},
            {'name': 'lore-and-worldbuilding', 'type': 15, 'gm_only': False},
            {'name': 'gm-planning', 'type': 15, 'gm_only': True}
        ]

# Load channels at module import time
DEFAULT_CAMPAIGN_CHANNELS = load_campaign_channels()
