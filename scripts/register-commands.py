#!/usr/bin/env python3
"""
Script to register Discord slash commands with Discord API.
Run this after deploying the Lambda function.
"""

import os
import sys
import asyncio
import discord
from discord.ext import commands

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import config


async def register_commands():
    """Register slash commands with Discord."""
    
    try:
        # Get Discord token
        token = config.get_discord_token()
        
        # Create bot instance
        intents = discord.Intents.default()
        bot = commands.Bot(command_prefix='!', intents=intents)
        
        @bot.event
        async def on_ready():
            print(f"✅ Logged in as {bot.user}")
            
            try:
                # Sync commands globally
                synced = await bot.tree.sync()
                print(f"✅ Synced {len(synced)} command(s) globally")
                
                # List synced commands
                for command in synced:
                    print(f"   - /{command.name}: {command.description}")
                
            except Exception as e:
                print(f"❌ Failed to sync commands: {e}")
            
            await bot.close()
        
        # Start bot
        await bot.start(token)
        
    except Exception as e:
        print(f"❌ Error registering commands: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("🔧 Registering Discord slash commands...")
    
    # Check environment variables
    if not os.getenv('DISCORD_BOT_TOKEN') and not os.path.exists('../.env'):
        print("❌ DISCORD_BOT_TOKEN not found in environment or .env file")
        print("   Please set it with: export DISCORD_BOT_TOKEN=your_token_here")
        sys.exit(1)
    
    # Run the registration
    asyncio.run(register_commands())
    print("✅ Command registration complete!")
