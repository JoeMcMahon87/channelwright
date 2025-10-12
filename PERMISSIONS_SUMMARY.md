# Campaign Permissions Summary

## Overview

The `/add-campaign` command creates a **fully private campaign environment** with role-based access control.

## Permission Hierarchy

### Level 1: Category (Private)
The campaign category is hidden from everyone except campaign members:

```
Category: "Campaign Name"
├─ @everyone: DENY VIEW_CHANNEL
└─ Campaign Members Role: ALLOW VIEW_CHANNEL
```

**Result:** Only users with the campaign role can see the category and its channels.

### Level 2: Regular Channels (Inherit)
Regular channels inherit category permissions:

```
Channel: "general", "session-notes", "voice-chat", etc.
└─ (inherits from category)
```

**Result:** All campaign role members can see these channels.

### Level 3: GM-Only Channels (Restricted)
GM-only channels override category permissions to restrict access:

```
Channel: "gm-notes", "gm-planning"
├─ @everyone: DENY VIEW_CHANNEL
├─ Campaign Members Role: DENY VIEW_CHANNEL (explicit override)
├─ Administrator Roles: ALLOW VIEW_CHANNEL
├─ GM Role: ALLOW VIEW_CHANNEL (if exists)
└─ Guild Owner: ALLOW VIEW_CHANNEL
```

**Result:** Only GMs, admins, and server owner can see these channels.

## Who Can See What?

### Regular Server Members (no campaign role)
- ❌ Cannot see the campaign category
- ❌ Cannot see any campaign channels
- The entire campaign is invisible to them

### Campaign Members (have campaign role)
- ✅ Can see the campaign category
- ✅ Can see regular channels (general, session-notes, voice-chat, etc.)
- ❌ Cannot see GM-only channels (gm-notes, gm-planning)

### Game Masters (have GM role or admin)
- ✅ Can see the campaign category
- ✅ Can see all regular channels
- ✅ Can see GM-only channels
- Full access to the entire campaign

### Server Owner
- ✅ Full access to everything (always)

## Permission Bits

The bot uses Discord's permission system:
- `VIEW_CHANNEL` = 1024 (0x400)
- `ADMINISTRATOR` = 8 (0x8)

## Example Scenarios

### Scenario 1: New Player Joins
1. Player joins Discord server
2. Player **cannot see** campaign category (no role)
3. GM assigns campaign role to player
4. Player **can now see** category and regular channels
5. Player **still cannot see** GM-only channels

### Scenario 2: GM Planning
1. GM wants to plan next session
2. GM goes to "gm-planning" forum channel
3. Only GM, admins, and owner can see this channel
4. Players with campaign role **cannot see** this channel
5. GM can discuss spoilers and plans privately

### Scenario 3: Multiple Campaigns
1. Server has "Campaign A" and "Campaign B"
2. Player has "Campaign A Members" role only
3. Player sees Campaign A category and channels
4. Player **cannot see** Campaign B at all
5. Each campaign is completely isolated

## Technical Implementation

### Category Creation
```python
permission_overwrites = [
    {"id": guild_id, "type": 0, "deny": "1024"},      # Deny @everyone
    {"id": role_id, "type": 0, "allow": "1024"}       # Allow campaign role
]
```

### Regular Channel Creation
```python
# No permission overwrites - inherits from category
permission_overwrites = []
```

### GM-Only Channel Creation
```python
permission_overwrites = [
    {"id": guild_id, "type": 0, "deny": "1024"},           # Deny @everyone
    {"id": campaign_role_id, "type": 0, "deny": "1024"},   # Deny campaign role
    {"id": admin_role_id, "type": 0, "allow": "1024"},     # Allow admins
    {"id": gm_role_id, "type": 0, "allow": "1024"}         # Allow GM role
]
# Note: Guild owner has implicit access, no explicit permission needed
```

## Benefits

1. **Privacy**: Campaigns are completely hidden from non-members
2. **Organization**: Each campaign is self-contained
3. **Security**: GM content is protected from players
4. **Flexibility**: Easy to add/remove members via role assignment
5. **Scalability**: Support multiple campaigns on one server

## Role Assignment

To give someone access to a campaign:
1. Right-click the user in Discord
2. Select "Roles"
3. Assign the "[Campaign Name] Members" role
4. User immediately gains access to the campaign

To remove access:
1. Remove the campaign role from the user
2. User immediately loses access to all campaign channels
