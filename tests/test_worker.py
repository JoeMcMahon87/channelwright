"""
Tests for the SQS channel creation worker
"""
import json
from unittest.mock import patch

from channelwright import worker


def sqs_event(message):
    return {'Records': [{'body': json.dumps(message)}]}


def test_progress_bar():
    assert worker.create_progress_bar(0, 4, width=4) == "[░░░░] 0% (0/4)"
    assert worker.create_progress_bar(2, 4, width=4) == "[██░░] 50% (2/4)"
    assert worker.create_progress_bar(4, 4, width=4) == "[████] 100% (4/4)"


@patch.object(worker.requests, 'post')
def test_create_channel_sets_parent_and_gm_topic(post):
    channel_config = {'name': 'gm-notes', 'type': 0, 'gm_only': True, 'description': 'Private notes'}

    worker.create_channel('111', channel_config, 'category-1', 'role-1', 'token')

    payload = post.call_args.kwargs['json']
    assert payload['name'] == 'gm-notes'
    assert payload['parent_id'] == 'category-1'
    assert payload['topic'].startswith('🔒 GM ONLY - Private notes')


@patch.object(worker, 'edit_original_response')
@patch.object(worker, 'create_channel', return_value={'id': 'chan-1', 'name': 'dice-rolls'})
def test_create_channel_task_reports_progress(create_channel, edit_response):
    message = {
        'task_type': 'create_channel',
        'application_id': 'app-123',
        'interaction_token': 'interaction-token',
        'guild_id': '111',
        'channel_config': {'name': 'dice-rolls', 'type': 0, 'gm_only': False},
        'category_id': 'category-1',
        'campaign_role_id': 'role-1',
        'current': 3,
        'total': 6,
        'campaign_name': 'Curse of Strahd'
    }

    worker.lambda_handler(sqs_event(message), None)

    create_channel.assert_called_once()
    content = edit_response.call_args.args[2]
    assert '50% (3/6)' in content
    assert 'dice-rolls' in content


@patch.object(worker, 'edit_original_response')
def test_complete_task_summarizes_channels(edit_response):
    message = {
        'task_type': 'complete',
        'application_id': 'app-123',
        'interaction_token': 'interaction-token',
        'campaign_name': 'Curse of Strahd',
        'role_name': 'Curse of Strahd Members',
        'created_channels': [
            {'name': 'general-discussion', 'type': 'Text', 'gm_only': False},
            {'name': 'gm-notes', 'type': 'Text', 'gm_only': True},
            {'name': 'campaign-main', 'type': 'Voice', 'gm_only': False}
        ]
    }

    worker.lambda_handler(sqs_event(message), None)

    content = edit_response.call_args.args[2]
    assert 'Created 3 channels' in content
    assert 'gm-notes 🔒' in content
    assert 'campaign-main' in content


@patch.object(worker, 'edit_original_response')
@patch.object(worker, 'create_channel', side_effect=RuntimeError('Missing Access'))
def test_failure_is_reported_to_discord(create_channel, edit_response):
    message = {
        'task_type': 'create_channel',
        'application_id': 'app-123',
        'interaction_token': 'interaction-token',
        'guild_id': '111',
        'channel_config': {'name': 'dice-rolls', 'type': 0},
        'category_id': 'category-1',
        'campaign_role_id': 'role-1',
        'current': 1,
        'total': 1,
        'campaign_name': 'Curse of Strahd'
    }

    worker.lambda_handler(sqs_event(message), None)

    content = edit_response.call_args.args[2]
    assert 'Error creating campaign' in content
    assert 'Missing Access' in content
