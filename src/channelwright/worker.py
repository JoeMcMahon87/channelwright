"""
Channel Creation Worker Lambda
Processes SQS messages to create channels and update progress
"""
import os
import json
import requests
from channelwright.campaign_config import get_channel_type_name


def edit_original_response(application_id, interaction_token, content):
    """
    Edit the original deferred interaction response
    """
    url = f"https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}/messages/@original"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "content": content
    }
    
    try:
        response = requests.patch(url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"Successfully edited original response")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error editing original response: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")


def create_progress_bar(current, total, width=20):
    """
    Create a text-based progress bar
    """
    filled = int((current / total) * width)
    bar = "█" * filled + "░" * (width - filled)
    percentage = int((current / total) * 100)
    return f"[{bar}] {percentage}% ({current}/{total})"


def create_channel(guild_id, channel_config, category_id, campaign_role_id, bot_token):
    """
    Create a channel with appropriate permissions
    """
    url = f"https://discord.com/api/v10/guilds/{guild_id}/channels"
    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json"
    }
    
    # All channels inherit category permissions
    permission_overwrites = []
    
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
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error creating channel {channel_config['name']}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        raise


def lambda_handler(event, context):
    """
    Process SQS messages to create channels
    """
    bot_token = os.environ.get('DISCORD_BOT_TOKEN')
    
    for record in event['Records']:
        try:
            # Parse message
            message = json.loads(record['body'])
            
            task_type = message['task_type']
            application_id = message['application_id']
            interaction_token = message['interaction_token']
            
            print(f"Processing task: {task_type}")
            
            if task_type == 'create_channel':
                # Extract channel creation data
                guild_id = message['guild_id']
                channel_config = message['channel_config']
                category_id = message['category_id']
                campaign_role_id = message['campaign_role_id']
                current = message['current']
                total = message['total']
                campaign_name = message['campaign_name']
                
                # Create the channel
                print(f"Creating channel: {channel_config['name']} ({current}/{total})")
                channel = create_channel(
                    guild_id=guild_id,
                    channel_config=channel_config,
                    category_id=category_id,
                    campaign_role_id=campaign_role_id,
                    bot_token=bot_token
                )
                
                print(f"Created channel: {channel['name']} (ID: {channel['id']})")
                
                # Update progress
                progress_bar = create_progress_bar(current, total)
                channel_type = get_channel_type_name(channel_config['type'])
                status_message = (
                    f"🏗️ **Creating Campaign: {campaign_name}**\n\n"
                    f"{progress_bar}\n\n"
                    f"✅ Created: **{channel_config['name']}** ({channel_type})"
                )
                
                edit_original_response(application_id, interaction_token, status_message)
                
            elif task_type == 'complete':
                # Final completion message
                campaign_name = message['campaign_name']
                role_name = message['role_name']
                created_channels = message['created_channels']
                
                # Build final success message
                channel_summary = f"✅ **Campaign Created: {campaign_name}**\n\n"
                channel_summary += f"**Role:** {role_name}\n\n"
                channel_summary += f"**Created {len(created_channels)} channels:**\n"
                
                # Add note about GM channels if any exist
                gm_channels_exist = any(c.get('gm_only') for c in created_channels)
                if gm_channels_exist:
                    channel_summary += "\n⚠️ _Channels marked 🔒 need manual GM-only setup_\n"
                
                # Group by type
                text_channels = [c for c in created_channels if c['type'] == 'Text']
                voice_channels = [c for c in created_channels if c['type'] == 'Voice']
                forum_channels = [c for c in created_channels if c['type'] == 'Forum']
                
                if text_channels:
                    channel_summary += "📝 Text:\n"
                    for ch in text_channels:
                        gm_tag = " 🔒" if ch.get('gm_only') else ""
                        channel_summary += f"  • {ch['name']}{gm_tag}\n"
                
                if voice_channels:
                    channel_summary += "🔊 Voice:\n"
                    for ch in voice_channels:
                        channel_summary += f"  • {ch['name']}\n"
                
                if forum_channels:
                    channel_summary += "💬 Forum:\n"
                    for ch in forum_channels:
                        gm_tag = " 🔒" if ch.get('gm_only') else ""
                        channel_summary += f"  • {ch['name']}{gm_tag}\n"
                
                edit_original_response(application_id, interaction_token, channel_summary)
                print(f"Campaign creation complete!")
                
        except Exception as e:
            print(f"Error processing message: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            
            # Try to send error message
            try:
                error_message = f"❌ **Error creating campaign**\n\nError: {str(e)}"
                edit_original_response(
                    message.get('application_id'),
                    message.get('interaction_token'),
                    error_message
                )
            except:
                print("Failed to send error message to Discord")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Processing complete')
    }
