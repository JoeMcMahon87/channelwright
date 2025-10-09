"""Discord bot implementation for ChannelWright."""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, List, Optional
import asyncio

from config import config
from database import db
from models import Campaign, ChannelTemplate, CampaignTemplate


class ChannelWrightBot(commands.Bot):
    """Main Discord bot class."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            application_id=config.discord_application_id
        )
    
    async def setup_hook(self):
        """Called when the bot is starting up."""
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")
        
        # Sync commands
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when the bot is ready."""
        print(f"Bot is ready! Logged in as {self.user}")


# Initialize bot instance
bot = ChannelWrightBot()


@bot.tree.command(name="begin-campaign", description="Create a new RPG campaign with organized channels")
@app_commands.describe(
    name="The name of the campaign",
    template="Channel template to use (default: default_template)"
)
async def begin_campaign(
    interaction: discord.Interaction,
    name: str,
    template: str = "default_template"
):
    """Create a new campaign with channels and roles."""
    
    # Defer the response since this might take a while
    await interaction.response.defer()
    
    guild = interaction.guild
    user = interaction.user
    
    # Validate inputs
    if not name or len(name.strip()) == 0:
        await interaction.followup.send("❌ Campaign name cannot be empty!", ephemeral=True)
        return
    
    # Clean up the campaign name for Discord
    campaign_name = name.strip()
    safe_name = "".join(c for c in campaign_name if c.isalnum() or c in (' ', '-', '_')).strip()
    
    if len(safe_name) > 100:
        await interaction.followup.send("❌ Campaign name is too long! Please use 100 characters or less.", ephemeral=True)
        return
    
    # Check if campaign already exists
    if await db.campaign_exists(str(guild.id), campaign_name):
        await interaction.followup.send(f"❌ A campaign named '{campaign_name}' already exists!", ephemeral=True)
        return
    
    try:
        # Get channel template
        templates = config.get_channel_templates()
        if template not in templates:
            template = "default_template"
        
        template_config = templates[template]
        campaign_template = CampaignTemplate(**template_config)
        
        # Create the role first
        role_name = f"{campaign_name} Members"
        role = await guild.create_role(
            name=role_name,
            reason=f"Campaign role created by {user.display_name}"
        )
        
        # Create category channel
        category = await guild.create_category(
            name=campaign_name,
            reason=f"Campaign category created by {user.display_name}"
        )
        
        # Set up permissions for the category
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.owner: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        
        await category.edit(overwrites=overwrites)
        
        # Create channels based on template
        created_channels = []
        
        for channel_template in campaign_template.channels:
            channel_overwrites = overwrites.copy()
            
            # If it's a private channel, restrict to guild owner only
            if channel_template.private:
                channel_overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    role: discord.PermissionOverwrite(read_messages=False),
                    guild.owner: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
                }
            
            # Create the channel based on type
            channel = None
            if channel_template.type == "text":
                channel = await guild.create_text_channel(
                    name=channel_template.name,
                    category=category,
                    topic=channel_template.description,
                    overwrites=channel_overwrites,
                    reason=f"Campaign channel created by {user.display_name}"
                )
            elif channel_template.type == "voice":
                channel = await guild.create_voice_channel(
                    name=channel_template.name,
                    category=category,
                    overwrites=channel_overwrites,
                    reason=f"Campaign channel created by {user.display_name}"
                )
            elif channel_template.type == "forum":
                channel = await guild.create_forum_channel(
                    name=channel_template.name,
                    category=category,
                    topic=channel_template.description,
                    overwrites=channel_overwrites,
                    reason=f"Campaign channel created by {user.display_name}"
                )
            
            if channel:
                created_channels.append({
                    "name": channel.name,
                    "id": str(channel.id),
                    "type": channel_template.type
                })
        
        # Save campaign to database
        campaign = Campaign(
            guild_id=str(guild.id),
            campaign_name=campaign_name,
            category_id=str(category.id),
            role_id=str(role.id),
            channels=created_channels,
            created_by=str(user.id),
            template_used=template
        )
        
        success = await db.save_campaign(campaign)
        
        if success:
            # Create success embed
            embed = discord.Embed(
                title="🎲 Campaign Created Successfully!",
                description=f"**{campaign_name}** is ready for adventure!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📁 Category",
                value=category.mention,
                inline=True
            )
            
            embed.add_field(
                name="👥 Role",
                value=role.mention,
                inline=True
            )
            
            embed.add_field(
                name="📊 Template",
                value=template,
                inline=True
            )
            
            # List created channels
            public_channels = [ch for ch in created_channels if not any(
                t.private for t in campaign_template.channels if t.name == ch["name"]
            )]
            private_channels = [ch for ch in created_channels if any(
                t.private for t in campaign_template.channels if t.name == ch["name"]
            )]
            
            if public_channels:
                channel_list = "\n".join([f"#{ch['name']}" for ch in public_channels])
                embed.add_field(
                    name="📢 Public Channels",
                    value=channel_list,
                    inline=True
                )
            
            if private_channels:
                channel_list = "\n".join([f"🔒 #{ch['name']}" for ch in private_channels])
                embed.add_field(
                    name="🔐 Private Channels",
                    value=channel_list,
                    inline=True
                )
            
            embed.add_field(
                name="🎯 Next Steps",
                value=f"• Assign the {role.mention} role to your players\n• Start planning your adventure!\n• Use the channels to organize your campaign",
                inline=False
            )
            
            embed.set_footer(text=f"Created by {user.display_name}")
            
            await interaction.followup.send(embed=embed)
            
        else:
            await interaction.followup.send("❌ Failed to save campaign data. Please try again.", ephemeral=True)
    
    except discord.Forbidden:
        await interaction.followup.send(
            "❌ I don't have permission to create channels and roles! Please make sure I have the following permissions:\n"
            "• Manage Channels\n• Manage Roles\n• View Channels",
            ephemeral=True
        )
    except Exception as e:
        print(f"Error creating campaign: {e}")
        await interaction.followup.send(
            f"❌ An error occurred while creating the campaign: {str(e)}",
            ephemeral=True
        )


@bot.tree.command(name="list-campaigns", description="List all campaigns in this server")
async def list_campaigns(interaction: discord.Interaction):
    """List all campaigns in the current guild."""
    await interaction.response.defer()
    
    guild = interaction.guild
    campaigns = await db.list_campaigns(str(guild.id))
    
    if not campaigns:
        embed = discord.Embed(
            title="📋 No Campaigns Found",
            description="No campaigns have been created in this server yet.\nUse `/begin-campaign` to create your first campaign!",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)
        return
    
    embed = discord.Embed(
        title="📋 Active Campaigns",
        description=f"Found {len(campaigns)} campaign(s) in this server:",
        color=discord.Color.blue()
    )
    
    for campaign in campaigns[:10]:  # Limit to 10 campaigns to avoid embed limits
        category = guild.get_channel(int(campaign.category_id))
        role = guild.get_role(int(campaign.role_id))
        
        category_name = category.name if category else "❌ Deleted"
        role_name = role.name if role else "❌ Deleted"
        
        embed.add_field(
            name=f"🎲 {campaign.campaign_name}",
            value=f"**Category:** {category_name}\n**Role:** {role_name}\n**Channels:** {len(campaign.channels)}",
            inline=True
        )
    
    if len(campaigns) > 10:
        embed.set_footer(text=f"Showing first 10 of {len(campaigns)} campaigns")
    
    await interaction.followup.send(embed=embed)
