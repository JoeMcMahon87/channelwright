# Campaign Setup Documentation

## Overview

The `/add-campaign` command creates a complete campaign infrastructure in Discord with proper permissions and organization.

## What Gets Created

### 1. Campaign Role
A role named `[Campaign Name] Members` that:
- Can be mentioned (@mention)
- Has no special permissions (basic member level)
- Grants access to the private campaign category and all non-GM channels

### 2. Private Channel Category
A **private** category (channel group) with the campaign name that:
- Is hidden from @everyone
- Is visible only to members with the campaign role
- Contains all campaign channels

### 3. Default Channels

The bot creates 7 channels organized by type:

#### Text Channels (📝)
- **general** - General campaign discussion
- **session-notes** - Session summaries and notes
- **gm-notes** 🔒 - Private GM planning and notes (GM-only)

#### Voice Channels (🔊)
- **voice-chat** - Voice channel for sessions

#### Forum Channels (💬)
- **character-sheets** - Character sheets and builds
- **lore-and-worldbuilding** - Campaign lore and world information
- **gm-planning** 🔒 - GM-only planning discussions (GM-only)

## Channel Permissions

### Category-Level Permissions
The entire category is **private**:
- ❌ **@everyone** - Cannot see the category or any channels
- ✅ **Campaign Role Members** - Can see the category and regular channels

### Regular Channels
- Inherit permissions from the category
- Visible to all campaign role members
- Hidden from everyone else

### GM-Only Channels 🔒
**Note:** Due to Discord's permission hierarchy, the bot cannot automatically restrict these channels. They are created with a warning in the description and must be manually configured by server admins.

**To configure GM-only channels:**
1. Right-click the channel (e.g., "gm-notes")
2. Select "Edit Channel" → "Permissions"
3. Remove or deny the campaign role
4. Add permissions for GM role, admin roles, or specific users

**Intended access:**
- ✅ **Guild Owner** - The server owner
- ✅ **Administrator Roles** - Any role with Administrator permission
- ✅ **GM Role** - If a role named "GM" exists in the server
- ❌ **Campaign Role Members** - Should be manually denied

## Customization

You can customize the default channels by editing `config/campaign_channels.yaml`:

```yaml
channels:
  - name: channel-name
    type: text  # or voice, forum
    gm_only: false  # or true for GM-only
    description: Channel description
  
  # Add more channels...
```

### Channel Types
- `text` - Text channel
- `voice` - Voice channel
- `forum` - Forum channel

After editing the YAML file, redeploy the bot for changes to take effect.

## Usage Example

```
/add-campaign name: Curse of Strahd
```

**Bot Response:**
```
✅ Created campaign: **Curse of Strahd**

**Role:** Curse of Strahd Members

**Channels:**
📝 Text:
  • general
  • session-notes
  • gm-notes 🔒
🔊 Voice:
  • voice-chat
💬 Forum:
  • character-sheets
  • lore-and-worldbuilding
  • gm-planning 🔒
```

## Required Bot Permissions

The bot needs these permissions to create campaigns:
- ✅ **Manage Channels** - To create categories and channels
- ✅ **Manage Roles** - To create the campaign role
- ✅ **View Server** - To read guild information

## Logging

All campaign creation steps are logged to CloudWatch for debugging:
- Guild information fetch
- Category creation
- Role creation
- Each channel creation with permissions
- Any errors with full tracebacks

View logs with:
```bash
aws logs tail /aws/lambda/discord_channelwright_bot --since 5m --follow
```

## Technical Details

### Permission Overwrites
- **Regular channels**: Grant VIEW_CHANNEL (1024) to campaign role
- **GM-only channels**: 
  - Deny VIEW_CHANNEL to @everyone
  - Allow VIEW_CHANNEL to guild owner (member type)
  - Allow VIEW_CHANNEL to administrator roles (role type)
  - Allow VIEW_CHANNEL to GM role if it exists (role type)

### API Calls Made
1. `GET /guilds/{guild_id}` - Fetch guild info and owner ID
2. `POST /guilds/{guild_id}/channels` - Create category
3. `POST /guilds/{guild_id}/roles` - Create campaign role
4. `GET /guilds/{guild_id}/roles` - Fetch roles for GM-only permission setup
5. `POST /guilds/{guild_id}/channels` - Create each channel (7 calls)

Total: 11 Discord API calls per campaign creation
