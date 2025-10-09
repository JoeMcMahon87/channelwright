# ChannelWright Commands

This document describes all available Discord commands for the ChannelWright bot.

## Available Commands

### `/begin-campaign`

Creates a new RPG campaign with organized channels and roles.

**Usage:**
```
/begin-campaign name:Campaign Name [template:template_name]
```

**Parameters:**
- `name` (required): The name of the campaign (max 100 characters)
- `template` (optional): Channel template to use (default: `default_template`)

**What it does:**
1. Creates a new Discord category with the campaign name
2. Creates a role named "{Campaign Name} Members"
3. Sets up category permissions for the new role
4. Creates channels based on the selected template
5. Sets up channel-specific permissions (public vs private)
6. Saves campaign data to the database

**Example:**
```
/begin-campaign name:Curse of Strahd template:default_template
```

**Permissions Required:**
- Manage Channels
- Manage Roles
- View Channels

### `/list-campaigns`

Lists all active campaigns in the current Discord server.

**Usage:**
```
/list-campaigns
```

**What it shows:**
- Campaign name
- Associated category channel
- Associated member role
- Number of channels created
- Creation status (if channels/roles still exist)

**Example Output:**
```
📋 Active Campaigns
Found 2 campaign(s) in this server:

🎲 Curse of Strahd
Category: Curse of Strahd
Role: Curse of Strahd Members
Channels: 6

🎲 Dragon Heist
Category: Dragon Heist
Role: Dragon Heist Members
Channels: 4
```

## Channel Templates

### Default Template (`default_template`)

The default template creates a comprehensive set of channels for most RPG campaigns:

**Public Channels** (accessible to campaign members):
- `#general` - Text channel for general campaign discussion
- `#character-sheets` - Forum channel for sharing and discussing character sheets
- `#session-recaps` - Forum channel for posting session summaries and recaps
- `#voice-chat` - Voice channel for game sessions

**Private Channels** (guild owner and GM only):
- `#gm-notes` - Text channel for GM planning and notes
- `#gm-resources` - Forum channel for GM-only resources and discussions

### Minimal Template (`minimal_template`)

A smaller template for simple campaigns:

**Public Channels:**
- `#campaign-chat` - Main campaign discussion
- `#voice-session` - Game session voice channel

**Private Channels:**
- `#gm-planning` - GM planning space

## Permission System

### Role Hierarchy

The bot creates a role hierarchy for each campaign:

1. **Guild Owner** - Full access to all channels and management
2. **{Campaign Name} Members** - Access to public campaign channels
3. **@everyone** - No access to campaign channels

### Channel Permissions

**Public Channels:**
- Guild Owner: Full permissions
- Campaign Members Role: Read, Send Messages, Connect (for voice)
- @everyone: No access

**Private Channels:**
- Guild Owner: Full permissions
- Campaign Members Role: No access
- @everyone: No access

### Bot Requirements

The bot must have the following permissions to function properly:

- **Manage Channels** - To create categories and channels
- **Manage Roles** - To create and assign campaign member roles
- **View Channels** - To see existing server structure
- **Send Messages** - To respond to commands
- **Use Slash Commands** - To register and respond to slash commands

**Important:** The bot's role must be positioned above any roles it creates in the server's role hierarchy.

## Error Handling

### Common Error Messages

**"Campaign name cannot be empty!"**
- The campaign name parameter is required and cannot be blank

**"Campaign name is too long!"**
- Campaign names must be 100 characters or less

**"A campaign named 'X' already exists!"**
- Each campaign name must be unique within a server

**"I don't have permission to create channels and roles!"**
- The bot lacks required permissions (see Bot Requirements above)

**"Application did not respond"**
- Usually indicates a configuration issue with the bot or AWS infrastructure

### Troubleshooting

1. **Commands not appearing:** Ensure slash commands are registered
2. **Permission errors:** Check bot role hierarchy and permissions
3. **Webhook errors:** Verify Discord webhook URL configuration
4. **Database errors:** Check AWS CloudWatch logs for details

## Usage Examples

### Setting up a D&D Campaign

```
/begin-campaign name:Lost Mine of Phandelver
```

This creates:
- Category: "Lost Mine of Phandelver"
- Role: "Lost Mine of Phandelver Members"
- 6 channels using the default template

### Creating a Simple Campaign

```
/begin-campaign name:One Shot Adventure template:minimal_template
```

This creates:
- Category: "One Shot Adventure"
- Role: "One Shot Adventure Members"
- 3 channels using the minimal template

### Checking Existing Campaigns

```
/list-campaigns
```

Shows all campaigns in the server with their current status.

## Future Commands (Planned)

### `/edit-campaign`
Edit an existing campaign's settings or channels.

### `/delete-campaign`
Remove a campaign and optionally delete its channels and role.

### `/assign-gm`
Assign GM role to a user for a specific campaign.

### `/campaign-info`
Show detailed information about a specific campaign.

These commands are planned for future releases and will provide more comprehensive campaign management capabilities.
