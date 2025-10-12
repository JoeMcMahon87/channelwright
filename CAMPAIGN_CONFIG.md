# Campaign Configuration Guide

## Overview

The bot uses a YAML configuration file to define which channels are created for each campaign. This allows you to customize the channel structure without modifying code.

## Configuration File

**Location:** `config/campaign_channels.yaml`

### Format

```yaml
channels:
  - name: channel-name
    type: text|voice|forum
    gm_only: true|false
    description: Channel description
```

### Channel Types

- **text** (type: 0) - Standard text channel
- **voice** (type: 2) - Voice channel for audio/video
- **forum** (type: 15) - Forum channel for threaded discussions

### GM-Only Channels

Channels with `gm_only: true` will have restricted permissions:
- Only users with the campaign role can view them
- Useful for GM planning, notes, and private discussions

## Current Configuration

The bot currently creates **11 channels** per campaign:

### Text Channels (7)
1. **general-discussion** - General campaign discussion
2. **session-recaps** - Notes and summaries from game sessions
3. **gm-notes** - Private GM notes and planning (GM-only)
4. **maps-and-visuals** - Post and discuss campaign maps and visuals
5. **session-zero** - Post and discuss session zero details
6. **safety** - Post and discuss safety and rules details
7. **dice-rolls** - Campaign dice rolls and results

### Voice Channels (1)
8. **campaign-main** - Voice channel for game sessions

### Forum Channels (3)
9. **characters-and-npcs** - Post and discuss character and NPCs sheets and info
10. **campaign-lore** - Discuss campaign lore and world details
11. **gm-planning** - GM-only planning and preparation (GM-only)

## Modifying the Configuration

### 1. Edit the YAML file

```bash
nano config/campaign_channels.yaml
```

### 2. Add, remove, or modify channels

Example - Adding a new channel:
```yaml
  - name: house-rules
    type: text
    gm_only: false
    description: Discuss and document house rules
```

### 3. Deploy the changes

```bash
./scripts/deploy-sqs.sh
```

The deployment script automatically copies the config to the Lambda package.

## Examples

### Adding a Private Voice Channel

```yaml
  - name: gm-voice
    type: voice
    gm_only: true
    description: Private voice channel for GMs
```

### Adding a Public Forum

```yaml
  - name: player-feedback
    type: forum
    gm_only: false
    description: Share feedback and suggestions
```

### Removing a Channel

Simply delete or comment out the channel entry:

```yaml
  # - name: dice-rolls
  #   type: text
  #   gm_only: false
  #   description: Campaign dice rolls and results
```

## Technical Details

### Configuration Loading

The configuration is loaded by `src/campaign_config.py`:
- Reads `config/campaign_channels.yaml`
- Converts YAML format to Discord API format
- Provides fallback configuration if file is missing

### Discord Channel Types

- Text: `type: 0`
- Voice: `type: 2`
- Forum: `type: 15`

### Permissions

GM-only channels (`gm_only: true`) are configured with:
- `@everyone` role: Deny view channel
- Campaign role: Allow view channel

This ensures only campaign members can see these channels.

## Best Practices

1. **Keep it organized** - Group related channels together
2. **Use descriptive names** - Use kebab-case (lowercase with hyphens)
3. **Limit channel count** - Too many channels can be overwhelming
4. **Test changes** - Create a test campaign after modifying config
5. **Document custom channels** - Add clear descriptions

## Troubleshooting

### Configuration not loading

Check Lambda logs:
```bash
aws logs tail /aws/lambda/discord_channelwright_bot --follow
```

### Channels not created

1. Verify YAML syntax is valid
2. Check that config is included in deployment
3. Ensure channel names are unique
4. Verify channel types are valid (text, voice, forum)

### Fallback Configuration

If the YAML file fails to load, the bot uses a default configuration with 7 channels:
- general, session-notes, gm-notes (text)
- voice-chat (voice)
- character-sheets, lore-and-worldbuilding, gm-planning (forum)
