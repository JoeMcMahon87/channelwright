"""
Discord Channelwright Bot - Main Handler
Uses SQS for async channel creation with progress updates
"""
import os
import json
import boto3
import requests
from discord_interactions import verify_key, InteractionType, InteractionResponseType
from campaign_config import DEFAULT_CAMPAIGN_CHANNELS

# Initialize SQS client
sqs = boto3.client('sqs')


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
        "mentionable": True
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
    
    # Verify request is from Discord
    public_key = os.environ.get('DISCORD_PUBLIC_KEY')
    
    try:
        if not verify_key(body.encode(), signature, timestamp, public_key):
            print(f"Signature verification failed. Signature: {signature}, Timestamp: {timestamp}")
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Invalid request signature'})
            }
    except Exception as e:
        print(f"Error during signature verification: {str(e)}")
        return {
            'statusCode': 401,
            'body': json.dumps({'error': 'Signature verification error'})
        }
    
    # Parse the request body
    body_json = json.loads(body)
    
    # Handle Discord PING for verification
    if body_json.get('type') == InteractionType.PING:
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
        
        if command_name == 'add-campaign':
            # Extract campaign name from options
            options = body_json.get('data', {}).get('options', [])
            campaign_name = None
            for option in options:
                if option.get('name') == 'name':
                    campaign_name = option.get('value')
                    break
            
            if not campaign_name:
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'type': InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        'data': {
                            'content': '❌ Campaign name is required!',
                            'flags': 64
                        }
                    })
                }
            
            print(f"Executing /add-campaign command")
            print(f"Campaign name from options: {campaign_name}")
            
            # Get guild ID
            guild_id = body_json.get('guild_id')
            if not guild_id:
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
            
            # Get Discord credentials
            bot_token = os.environ.get('DISCORD_BOT_TOKEN')
            application_id = body_json.get('application_id')
            interaction_token = body_json.get('token')
            queue_url = os.environ.get('SQS_QUEUE_URL')
            
            print(f"Starting campaign creation for: {campaign_name}")
            print(f"Application ID: {application_id}")
            print(f"Queue URL: {queue_url}")
            
            try:
                # Step 1: Create role and category immediately
                role_name = f"{campaign_name} Members"
                print(f"Creating role '{role_name}'")
                role = create_role(guild_id, role_name, bot_token)
                role_id = role.get('id')
                print(f"Created role: {role_id}")
                
                print(f"Creating private category '{campaign_name}'")
                category = create_channel_category(guild_id, campaign_name, role_id, bot_token)
                category_id = category.get('id')
                print(f"Created category: {category_id}")
                
                # Step 2: Queue channel creation tasks
                total_channels = len(DEFAULT_CAMPAIGN_CHANNELS)
                print(f"Queuing {total_channels} channel creation tasks")
                
                for idx, channel_config in enumerate(DEFAULT_CAMPAIGN_CHANNELS, start=1):
                    message = {
                        'task_type': 'create_channel',
                        'application_id': application_id,
                        'interaction_token': interaction_token,
                        'guild_id': guild_id,
                        'channel_config': channel_config,
                        'category_id': category_id,
                        'campaign_role_id': role_id,
                        'current': idx,
                        'total': total_channels,
                        'campaign_name': campaign_name
                    }
                    
                    sqs.send_message(
                        QueueUrl=queue_url,
                        MessageBody=json.dumps(message)
                    )
                    print(f"Queued channel {idx}/{total_channels}: {channel_config['name']}")
                
                # Queue completion message
                completion_message = {
                    'task_type': 'complete',
                    'application_id': application_id,
                    'interaction_token': interaction_token,
                    'campaign_name': campaign_name,
                    'role_name': role_name,
                    'created_channels': [
                        {
                            'name': ch['name'],
                            'type': 'Text' if ch['type'] == 0 else ('Voice' if ch['type'] == 2 else 'Forum'),
                            'gm_only': ch.get('gm_only', False)
                        }
                        for ch in DEFAULT_CAMPAIGN_CHANNELS
                    ]
                }
                
                sqs.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json.dumps(completion_message),
                    DelaySeconds=total_channels * 2  # Delay to ensure all channels are created first
                )
                
                print(f"All tasks queued successfully")
                
                # Step 3: Return deferred response immediately
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'type': 5  # DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
                    })
                }
                
            except Exception as e:
                print(f"ERROR in campaign setup: {str(e)}")
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
                            'flags': 64
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
