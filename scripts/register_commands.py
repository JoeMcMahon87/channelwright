"""
Register slash commands with Discord
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DISCORD_APP_ID = os.environ.get('DISCORD_APPLICATION_ID')
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

# Discord API endpoint for global commands
url = f"https://discord.com/api/v10/applications/{DISCORD_APP_ID}/commands"

# Define the commands
commands = [
    {
        "name": "hellobot",
        "description": "Get a friendly hello from the bot!",
        "type": 1  # CHAT_INPUT
    },
    {
        "name": "add-campaign",
        "description": "Create a new campaign channel category",
        "type": 1,  # CHAT_INPUT
        "options": [
            {
                "name": "name",
                "description": "The name of the campaign",
                "type": 3,  # STRING
                "required": True
            }
        ]
    }
]

def register_commands():
    """Register commands with Discord"""
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    for command in commands:
        response = requests.post(url, json=command, headers=headers)
        
        if response.status_code == 200 or response.status_code == 201:
            print(f"✓ Successfully registered command: /{command['name']}")
        else:
            print(f"✗ Failed to register command: /{command['name']}")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text}")

if __name__ == '__main__':
    if not DISCORD_APP_ID or not DISCORD_BOT_TOKEN:
        print("Error: DISCORD_APP_ID and DISCORD_BOT_TOKEN must be set in .env file")
        exit(1)
    
    print("Registering Discord slash commands...")
    register_commands()
    print("\nDone! Commands may take a few minutes to appear in Discord.")
