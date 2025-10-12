"""
Discord Hello Bot - Main Handler
{{ ... }}
Uses discord-interactions for serverless Discord bot
"""
import os
import json
import requests
from discord_interactions import verify_key, InteractionType, InteractionResponseType
from campaign_config import DEFAULT_CAMPAIGN_CHANNELS, get_channel_type_name


def create_channel_category(guild_id, category_name, campaign_role_id, bot_token):
    """
    Create a private Discord channel category with campaign role access
    """
    url = f"https://discord.com/api/v10/guilds/{guild_id}/channels"
    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json"
    }
    
    # Make category private: deny @everyone, allow campaign role
    permission_overwrites = [
        {
            "id": guild_id,  # @everyone role (same ID as guild)
            "type": 0,  # Role type
            "deny": "1024"  # Deny VIEW_CHANNEL (1024)
        },
        {
            "id": campaign_role_id,  # Campaign role
            "type": 0,  # Role type
            "allow": "1024"  # Allow VIEW_CHANNEL
        }
    ]
    
    payload = {
        "name": category_name,
        "type": 4,  # 4 = GUILD_CATEGORY
        "permission_overwrites": permission_overwrites
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error creating category: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        raise


def create_role(guild_id, role_name, bot_token):
    """
    Create a Discord role using Discord API
    """
    url = f"https://discord.com/api/v10/guilds/{guild_id}/roles"
    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "name": role_name,
        "permissions": "0",  # No special permissions
        "color": 0,  # Default color
        "hoist": False,  # Don't display separately in member list
        "mentionable": True  # Allow role to be mentioned
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error creating role: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        raise


def get_guild_info(guild_id, bot_token):
    """
    Get guild information including owner ID
    """
    url = f"https://discord.com/api/v10/guilds/{guild_id}"
    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching guild info: {e}")
        return None


def get_guild_roles(guild_id, bot_token):
    """
    Get all roles in a guild
    """
    url = f"https://discord.com/api/v10/guilds/{guild_id}/roles"
    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching guild roles: {e}")
        return []


def create_channel(guild_id, channel_config, category_id, campaign_role_id, bot_token):
    """
    Create a channel with appropriate permissions
    
    Args:
        guild_id: Discord guild ID
        channel_config: Dict with 'name', 'type', 'gm_only', 'description'
        category_id: ID of the parent category
        campaign_role_id: ID of the campaign members role
        bot_token: Discord bot token
    """
    url = f"https://discord.com/api/v10/guilds/{guild_id}/channels"
    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json"
    }
    
    # Build permission overwrites
    permission_overwrites = []
    
    # GM-only channels: Due to Discord permission hierarchy limitations,
    # the bot cannot automatically restrict channels from the campaign role it creates.
    # GM channels are created as regular channels - admins must manually configure permissions.
    # All channels inherit category permissions (visible to campaign members only)
    
    payload = {
        "name": channel_config['name'],
        "type": channel_config['type'],
        "parent_id": category_id,
        "permission_overwrites": permission_overwrites
    }
    
    # Add topic/description for text and forum channels
    if channel_config['type'] in [0, 15] and channel_config.get('description'):
        description = channel_config['description']
        # Add GM-only note to description
        if channel_config.get('gm_only'):
            description = f"🔒 GM ONLY - {description}\n\n⚠️ Admins: Please manually restrict this channel to GMs only."
        payload['topic'] = description
    
    # Debug logging
    print(f"Channel payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error creating channel {channel_config['name']}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        print(f"Permission overwrites attempted: {permission_overwrites}")
        raise


def lambda_handler(event, context):
    """
    AWS Lambda handler for Discord interactions
    """
    # Get headers (handle both lowercase and mixed case)
    headers = event.get('headers', {})
    
    # API Gateway can provide headers in different cases, so check both
    signature = headers.get('x-signature-ed25519') or headers.get('X-Signature-Ed25519')
    timestamp = headers.get('x-signature-timestamp') or headers.get('X-Signature-Timestamp')
    body = event.get('body', '')
    
    # Check if required headers are present
    if not signature or not timestamp:
        print(f"Missing required headers. Signature: {signature}, Timestamp: {timestamp}")
        return {
            'statusCode': 401,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': 'Missing signature headers'})
        }
    
    # Verify request is from Discord
    public_key = os.environ.get('DISCORD_PUBLIC_KEY')
    
    if not public_key:
        print("DISCORD_PUBLIC_KEY environment variable not set")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': 'Server configuration error'})
        }
    
    try:
        if not verify_key(body.encode(), signature, timestamp, public_key):
            print(f"Signature verification failed. Signature: {signature[:20]}..., Timestamp: {timestamp}")
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': 'Invalid request signature'})
            }
    except Exception as e:
        print(f"Error during signature verification: {str(e)}")
        return {
            'statusCode': 401,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': 'Signature verification error'})
        }
    
    # Parse the request body
    body_json = json.loads(body)
    
    print(f"Received interaction type: {body_json.get('type')}")
    
    # Handle Discord PING for verification
    if body_json.get('type') == InteractionType.PING:
        print("Handling PING request for endpoint verification")
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'type': InteractionResponseType.PONG
            })
        }
    
    # Handle slash commands
    if body_json.get('type') == InteractionType.APPLICATION_COMMAND:
        command_name = body_json.get('data', {}).get('name')
        print(f"Processing command: /{command_name}")
        
        if command_name == 'hellobot':
            print("Executing /hellobot command")
            # Get the user's name from the interaction
            user = body_json.get('member', {}).get('user', {}) or body_json.get('user', {})
            username = user.get('username', 'friend')
            print(f"Responding to user: {username}")
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'type': InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    'data': {
                        'content': f'Hello {username}! 👋'
                    }
                })
            }
        
        if command_name == 'add-campaign':
            print("Executing /add-campaign command")
            # Get the campaign name from command options
            options = body_json.get('data', {}).get('options', [])
            campaign_name = None
            for option in options:
                if option.get('name') == 'name':
                    campaign_name = option.get('value')
                    break
            
            print(f"Campaign name from options: {campaign_name}")
            
            if not campaign_name:
                print("ERROR: Campaign name is missing")
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'type': InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        'data': {
                            'content': '❌ Campaign name is required!',
                            'flags': 64  # Ephemeral message (only visible to user)
                        }
                    })
                }
            
            # Get guild ID
            guild_id = body_json.get('guild_id')
            print(f"Guild ID: {guild_id}")
            
            if not guild_id:
                print("ERROR: Guild ID is missing (command not used in a server)")
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'type': InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        'data': {
                            'content': '❌ This command can only be used in a server!',
                            'flags': 64
                        }
                    })
                }
            
            # Create campaign synchronously and return the result directly
            # Since Lambda doesn't support true async after return, we do all the work
            # and return a normal response (type 4) with the results
            # Lambda timeout is 30 seconds which is enough for channel creation
            
            bot_token = os.environ.get('DISCORD_BOT_TOKEN')
            
            print(f"Starting campaign creation for: {campaign_name}")
            
            try:
                # Create the role FIRST (needed for category permissions)
                role_name = f"{campaign_name} Members"
                print(f"Creating role '{role_name}'")
                role = create_role(guild_id, role_name, bot_token)
                role_id = role.get('id')
                print(f"Created role: {role_id}")
                
                # Create the private category with campaign role access
                print(f"Creating private category '{campaign_name}'")
                category = create_channel_category(guild_id, campaign_name, role_id, bot_token)
                category_id = category.get('id')
                print(f"Created category: {category_id}")
                
                # Create channels from config
                created_channels = []
                print(f"Creating {len(DEFAULT_CAMPAIGN_CHANNELS)} channels...")
                for channel_config in DEFAULT_CAMPAIGN_CHANNELS:
                    print(f"Creating {get_channel_type_name(channel_config['type'])} channel: {channel_config['name']}")
                    channel = create_channel(
                        guild_id=guild_id,
                        channel_config=channel_config,
                        category_id=category_id,
                        campaign_role_id=role_id,
                        bot_token=bot_token
                    )
                    created_channels.append({
                        'name': channel['name'],
                        'type': get_channel_type_name(channel_config['type']),
                        'gm_only': channel_config['gm_only']
                    })
                    print(f"Created: {channel['name']} (ID: {channel['id']})")
                
                # Build success message
                channel_summary = f"✅ **Campaign Created: {campaign_name}**\n\n"
                channel_summary += f"**Role:** {role_name}\n\n"
                channel_summary += f"**Created {len(created_channels)} channels:**\n"
                
                # Add note about GM channels if any exist
                gm_channels_exist = any(c['gm_only'] for c in created_channels)
                if gm_channels_exist:
                    channel_summary += "\n⚠️ _Channels marked 🔒 need manual GM-only setup_\n"
                
                # Group by type
                text_channels = [c for c in created_channels if c['type'] == 'Text']
                voice_channels = [c for c in created_channels if c['type'] == 'Voice']
                forum_channels = [c for c in created_channels if c['type'] == 'Forum']
                
                if text_channels:
                    channel_summary += "📝 Text:\n"
                    for ch in text_channels:
                        gm_tag = " 🔒" if ch['gm_only'] else ""
                        channel_summary += f"  • {ch['name']}{gm_tag}\n"
                
                if voice_channels:
                    channel_summary += "🔊 Voice:\n"
                    for ch in voice_channels:
                        channel_summary += f"  • {ch['name']}\n"
                
                if forum_channels:
                    channel_summary += "💬 Forum:\n"
                    for ch in forum_channels:
                        gm_tag = " 🔒" if ch['gm_only'] else ""
                        channel_summary += f"  • {ch['name']}{gm_tag}\n"
                
                print(f"Campaign creation complete!")
                
                # Return normal response with results
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'type': InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        'data': {
                            'content': channel_summary
                        }
                    })
                }
                
            except Exception as e:
                print(f"ERROR in campaign creation: {str(e)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'type': InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        'data': {
                            'content': f'❌ **Failed to create campaign: {campaign_name}**\n\nError: {str(e)}',
                            'flags': 64  # Ephemeral
                        }
                    })
                }
    
    # Default response for unknown interactions
    print(f"Unknown interaction type or command. Body: {body_json}")
    return {
        'statusCode': 400,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({'error': 'Unknown interaction type'})
    }


def local_handler(request_data):
    """
    Local testing handler (non-Lambda)
    """
    event = {
        'body': json.dumps(request_data)
    }
    return lambda_handler(event, None)


if __name__ == '__main__':
    # Test the bot locally
    print("Testing hello bot...")
    
    # Simulate a PING interaction
    ping_response = local_handler({'type': InteractionType.PING})
    print(f"PING Response: {ping_response}")
    
    # Simulate a /hellobot command
    command_response = local_handler({
        'type': InteractionType.APPLICATION_COMMAND,
        'data': {'name': 'hellobot'},
        'user': {'username': 'TestUser'}
    })
    print(f"Command Response: {command_response}")
