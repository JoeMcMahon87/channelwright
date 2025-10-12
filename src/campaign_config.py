"""
Campaign channel configuration
Loads channel definitions from YAML config file
"""
import os
import yaml

# Channel types
CHANNEL_TYPE_TEXT = 0
CHANNEL_TYPE_VOICE = 2
CHANNEL_TYPE_FORUM = 15

# Map string types to Discord channel type integers
CHANNEL_TYPE_MAP = {
    'text': CHANNEL_TYPE_TEXT,
    'voice': CHANNEL_TYPE_VOICE,
    'forum': CHANNEL_TYPE_FORUM
}


def load_campaign_channels():
    """Load campaign channel configuration from YAML file"""
    # In Lambda, files are at /var/task/, so config is at /var/task/config/
    # Locally, we're in src/, so config is at ../config/
    # Try Lambda path first, then local path
    lambda_config = '/var/task/config/campaign_channels.yaml'
    local_config = os.path.join(os.path.dirname(__file__), '..', 'config', 'campaign_channels.yaml')
    
    config_file = lambda_config if os.path.exists(lambda_config) else local_config
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Convert string types to integers
        channels = []
        for channel in config.get('channels', []):
            channel_type_str = channel.get('type', 'text').lower()
            channel_copy = channel.copy()
            channel_copy['type'] = CHANNEL_TYPE_MAP.get(channel_type_str, CHANNEL_TYPE_TEXT)
            channels.append(channel_copy)
        
        return channels
    except Exception as e:
        print(f"Error loading campaign channels config: {e}")
        # Return minimal default if config fails to load
        return [
            {
                "name": "general",
                "type": CHANNEL_TYPE_TEXT,
                "gm_only": False,
                "description": "General campaign discussion"
            }
        ]


# Load channels on module import
DEFAULT_CAMPAIGN_CHANNELS = load_campaign_channels()


def get_channel_type_name(channel_type):
    """Get human-readable name for channel type"""
    type_names = {
        CHANNEL_TYPE_TEXT: "Text",
        CHANNEL_TYPE_VOICE: "Voice",
        CHANNEL_TYPE_FORUM: "Forum"
    }
    return type_names.get(channel_type, "Unknown")
