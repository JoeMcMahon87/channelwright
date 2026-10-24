"""
Tests for campaign channel configuration loading
"""
import pytest
import yaml

from channelwright.campaign_config import get_channel_type_name, load_campaign_channels


def test_channel_type_names():
    assert get_channel_type_name(0) == 'Text'
    assert get_channel_type_name(2) == 'Voice'
    assert get_channel_type_name(15) == 'Forum'
    assert get_channel_type_name(99) == 'Unknown'


def test_loads_every_channel_from_yaml():
    with open('config/campaign_channels.yaml') as f:
        expected = yaml.safe_load(f)['channels']

    channels = load_campaign_channels()

    assert [c['name'] for c in channels] == [c['name'] for c in expected]


def test_maps_yaml_types_to_discord_types():
    channels = {c['name']: c for c in load_campaign_channels()}

    assert channels['general-discussion']['type'] == 0
    assert channels['campaign-main']['type'] == 2
    assert channels['campaign-lore']['type'] == 15


def test_preserves_gm_only_flag():
    channels = {c['name']: c for c in load_campaign_channels()}

    assert channels['gm-notes']['gm_only'] is True
    assert channels['general-discussion']['gm_only'] is False


@pytest.mark.xfail(strict=True, reason="Known bug: descriptions are dropped (review item 3)")
def test_preserves_description():
    channels = {c['name']: c for c in load_campaign_channels()}

    assert channels['gm-notes']['description'] == 'Private GM notes and planning'
