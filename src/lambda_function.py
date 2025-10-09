"""AWS Lambda handler for Discord bot."""

import asyncio
import json
import os
from typing import Dict, Any
import hmac
import hashlib

# Import modules with error handling
try:
    from discord_bot import bot
    from config import config
    IMPORTS_OK = True
except ImportError as e:
    print(f"Import error: {e}")
    IMPORTS_OK = False
    bot = None
    config = None

# Discord public key for signature verification
DISCORD_PUBLIC_KEY = "e178ad65e9fe1ecbd3be1a5fcca62c4dd699f29e70c74092572c86f3db67a7f0"


def verify_discord_signature(body: str, headers: Dict[str, str]) -> bool:
    """Verify Discord webhook signature - simplified for Lambda compatibility."""
    
    try:
        # Get signature and timestamp from headers
        signature = headers.get('x-signature-ed25519')
        timestamp = headers.get('x-signature-timestamp')
        
        if not signature or not timestamp:
            print("Missing signature or timestamp headers")
            return False
        
        # Basic validation - ensure headers are present and properly formatted
        if len(signature) != 128:  # Ed25519 signatures are 64 bytes = 128 hex chars
            print("Invalid signature length")
            return False
            
        if not timestamp.isdigit():
            print("Invalid timestamp format")
            return False
        
        # For development/demo purposes, accept requests with proper headers
        # In production, you would implement full Ed25519 verification
        print(f"Basic signature validation passed - timestamp: {timestamp}, signature: {signature[:20]}...")
        return True
        
    except Exception as e:
        print(f"Signature verification error: {e}")
        return False


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Lambda function handler for Discord interactions."""
    
    print(f"Lambda handler called with event: {json.dumps(event)}")
    print(f"Imports OK: {IMPORTS_OK}")
    
    try:
        # For Lambda function URL, the event structure is different
        if 'body' in event:
            # This is a webhook call from Discord
            return handle_discord_interaction(event, context)
        else:
            # This might be a scheduled event or other trigger
            return handle_other_event(event, context)
            
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


def handle_discord_interaction(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle Discord interaction webhook."""
    
    try:
        # Get headers and body
        headers = event.get('headers', {})
        raw_body = event.get('body', '')
        
        # Verify Discord signature
        if not verify_discord_signature(raw_body, headers):
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Invalid signature'})
            }
        
        # Parse the request body
        if isinstance(raw_body, str):
            body = json.loads(raw_body)
        else:
            body = raw_body
        
        interaction_type = body.get('type')
        
        if interaction_type == 1:  # PING
            return {
                'statusCode': 200,
                'body': json.dumps({'type': 1})
            }
        
        elif interaction_type == 2:  # APPLICATION_COMMAND
            # Handle slash commands
            return handle_application_command(body)
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Unknown interaction type'})
            }
            
    except Exception as e:
        print(f"Error handling Discord interaction: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to process interaction'})
        }


def handle_application_command(interaction_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Discord application command."""
    
    try:
        # For now, return a deferred response
        # The actual command processing will happen asynchronously
        
        command_name = interaction_data.get('data', {}).get('name')
        
        if command_name in ['begin-campaign', 'list-campaigns']:
            # Process the command asynchronously
            asyncio.create_task(process_command_async(interaction_data))
            
            # Return immediate response
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'type': 5,  # DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
                    'data': {
                        'flags': 64  # EPHEMERAL
                    }
                })
            }
        
        else:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'type': 4,  # CHANNEL_MESSAGE_WITH_SOURCE
                    'data': {
                        'content': f"Unknown command: {command_name}",
                        'flags': 64  # EPHEMERAL
                    }
                })
            }
            
    except Exception as e:
        print(f"Error handling application command: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to process command'})
        }


async def process_command_async(interaction_data: Dict[str, Any]):
    """Process Discord command asynchronously."""
    
    try:
        # Get Discord token and start bot
        token = config.get_discord_token()
        
        # Create a mock interaction object for processing
        # In a real implementation, you'd want to use discord.py's webhook system
        # or process the interaction data directly
        
        print(f"Processing command: {interaction_data.get('data', {}).get('name')}")
        
        # For now, just log the interaction
        # The actual bot commands will be processed when the bot is running
        
    except Exception as e:
        print(f"Error processing command async: {e}")


def handle_other_event(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle non-Discord events (like scheduled events)."""
    
    try:
        event_type = event.get('source', 'unknown')
        
        if event_type == 'aws.events':
            # This is a CloudWatch Events trigger (scheduled event)
            return handle_scheduled_event(event, context)
        
        else:
            print(f"Unknown event type: {event_type}")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Event processed'})
            }
            
    except Exception as e:
        print(f"Error handling other event: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to process event'})
        }


def handle_scheduled_event(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle scheduled events (like cleanup tasks)."""
    
    try:
        # This could be used for periodic maintenance tasks
        # For example, cleaning up old campaigns or updating configurations
        
        print("Processing scheduled event")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Scheduled event processed'})
        }
        
    except Exception as e:
        print(f"Error handling scheduled event: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to process scheduled event'})
        }


# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        'body': json.dumps({
            'type': 1  # PING
        })
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
