"""
Discord Hello Bot - Main Handler
Uses discord-interactions for serverless Discord bot
"""
import os
import json
from discord_interactions import (
    verify_key,
    InteractionType,
    InteractionResponseType,
)


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
        
        if command_name == 'hellobot':
            # Get the user's name from the interaction
            user = body_json.get('member', {}).get('user', {}) or body_json.get('user', {})
            username = user.get('username', 'friend')
            
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
    
    # Default response for unknown interactions
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
