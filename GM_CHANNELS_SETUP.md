# GM-Only Channels - Manual Setup Required

## Why Manual Setup is Needed

Due to Discord's permission hierarchy system, bots cannot automatically configure permissions for roles they create. Specifically:

1. **Role Hierarchy**: A bot can only manage roles that are **below** its own role in the server's role list
2. **New Roles**: When the bot creates the campaign role, it's often placed above the bot's role
3. **Permission Conflict**: The bot cannot deny permissions for a role it cannot manage

## What the Bot Creates

The bot creates all channels (including GM-only ones) with:
- ✅ **Private category** - Hidden from @everyone
- ✅ **Campaign role access** - All channels visible to campaign members
- ⚠️ **GM channels marked** - Description includes "🔒 GM ONLY" warning

## Manual Configuration Steps

### Step 1: Identify GM Channels

GM channels are marked with 🔒 in their description:
- `gm-notes` - 🔒 GM ONLY - Private GM planning and notes
- `gm-planning` - 🔒 GM ONLY - GM-only planning discussions

### Step 2: Configure Each GM Channel

For each GM channel (e.g., `gm-notes`):

1. **Right-click the channel** → Select "Edit Channel"

2. **Go to Permissions tab**

3. **Remove campaign role access:**
   - Find the campaign role (e.g., "My Campaign Members")
   - Click the X to remove it, OR
   - Click the role and set "View Channel" to ❌ (deny)

4. **Add GM access** (choose one or more):
   
   **Option A: Use existing GM role**
   - Click "Add members or roles"
   - Select your "GM" role
   - Set "View Channel" to ✅ (allow)
   
   **Option B: Add specific users**
   - Click "Add members or roles"
   - Select the GM user(s)
   - Set "View Channel" to ✅ (allow)
   
   **Option C: Create a GM role**
   - Go to Server Settings → Roles
   - Create a new "GM" role
   - Assign it to GMs
   - Return to channel permissions and add this role

5. **Save changes**

### Step 3: Verify Permissions

Test with a campaign member account:
- ✅ Can see regular channels (general, session-notes, etc.)
- ❌ Cannot see GM channels (gm-notes, gm-planning)

Test with a GM account:
- ✅ Can see all channels including GM-only

## Quick Permission Template

For each GM channel, the permissions should look like:

```
Channel: gm-notes

Permissions:
├─ @everyone: ❌ View Channel (inherited from category)
├─ Campaign Members Role: ❌ View Channel (DENY - manual)
├─ GM Role: ✅ View Channel (ALLOW - manual)
└─ Admins: ✅ View Channel (implicit - have Administrator permission)
```

## Alternative: Don't Use GM Channels

If manual configuration is too much work, you can:

1. **Edit `config/campaign_channels.yaml`**
2. **Remove GM-only channels** or set `gm_only: false`
3. **Redeploy the bot**
4. **Create GM channels manually** in a separate category

Example simplified config:
```yaml
channels:
  - name: general
    type: text
    gm_only: false
    description: General campaign discussion
  
  - name: session-notes
    type: text
    gm_only: false
    description: Session summaries and notes
  
  # Remove gm-notes and gm-planning
```

## Future Improvement

To enable automatic GM channel restriction, the bot would need:

1. **Higher role placement**: Manually move the bot's role above the campaign role in Server Settings → Roles
2. **Code update**: Re-enable permission overwrites in the bot code

However, this requires manual server configuration for each installation, which defeats the purpose of automation.

## Summary

- ✅ **Bot creates** all channels including GM-marked ones
- ⚠️ **Manual step required** to restrict GM channels
- 🔒 **Look for** channels with "🔒 GM ONLY" in description
- ⚙️ **Configure** by denying campaign role and allowing GM role
- 🎯 **Takes ~2 minutes** per campaign after creation
