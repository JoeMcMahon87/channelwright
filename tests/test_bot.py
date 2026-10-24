"""
Tests for the Discord interaction handler
"""
import json
from unittest.mock import patch

from discord_interactions import InteractionResponseType, InteractionType

from channelwright import bot
from channelwright.campaign_config import DEFAULT_CAMPAIGN_CHANNELS


def add_campaign_payload(name='Curse of Strahd', guild_id='111'):
    payload = {
        'type': InteractionType.APPLICATION_COMMAND,
        'application_id': 'app-123',
        'token': 'interaction-token',
        'data': {
            'name': 'add-campaign',
            'options': [{'name': 'name', 'value': name}]
        }
    }
    if guild_id:
        payload['guild_id'] = guild_id
    return payload


def test_ping_returns_pong(signed_event):
    response = bot.lambda_handler(signed_event({'type': InteractionType.PING}), None)

    assert response['statusCode'] == 200
    assert json.loads(response['body'])['type'] == InteractionResponseType.PONG


def test_rejects_bad_signature(signed_event):
    event = signed_event({'type': InteractionType.PING})
    event['body'] = json.dumps({'type': InteractionType.PING, 'tampered': True})

    response = bot.lambda_handler(event, None)

    assert response['statusCode'] == 401


def test_rejects_missing_signature():
    event = {'headers': {}, 'body': json.dumps({'type': InteractionType.PING})}

    response = bot.lambda_handler(event, None)

    assert response['statusCode'] == 401


def test_unknown_command_returns_400(signed_event):
    payload = {'type': InteractionType.APPLICATION_COMMAND, 'data': {'name': 'no-such-command'}}

    response = bot.lambda_handler(signed_event(payload), None)

    assert response['statusCode'] == 400


def test_add_campaign_outside_server_is_rejected(signed_event):
    response = bot.lambda_handler(signed_event(add_campaign_payload(guild_id=None)), None)

    body = json.loads(response['body'])
    assert 'only be used in a server' in body['data']['content']
    assert body['data']['flags'] == 64


@patch.object(bot, 'sqs')
@patch.object(bot, 'create_channel_category', return_value={'id': 'category-1'})
@patch.object(bot, 'create_role', return_value={'id': 'role-1'})
def test_add_campaign_queues_channels_and_defers(create_role, create_category, sqs, signed_event):
    response = bot.lambda_handler(signed_event(add_campaign_payload()), None)

    assert json.loads(response['body'])['type'] == 5  # DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
    create_role.assert_called_once_with('111', 'Curse of Strahd Members', 'test-bot-token')
    create_category.assert_called_once_with('111', 'Curse of Strahd', 'role-1', 'test-bot-token')

    messages = [json.loads(c.kwargs['MessageBody']) for c in sqs.send_message.call_args_list]
    channel_tasks = [m for m in messages if m['task_type'] == 'create_channel']
    assert [m['channel_config']['name'] for m in channel_tasks] == [c['name'] for c in DEFAULT_CAMPAIGN_CHANNELS]
    assert all(m['category_id'] == 'category-1' for m in channel_tasks)
    assert messages[-1]['task_type'] == 'complete'


@patch.object(bot, 'sqs')
@patch.object(bot, 'create_role', side_effect=RuntimeError('Missing Permissions'))
def test_add_campaign_reports_setup_failure(create_role, sqs, signed_event):
    response = bot.lambda_handler(signed_event(add_campaign_payload()), None)

    body = json.loads(response['body'])
    assert 'Failed to create campaign' in body['data']['content']
    sqs.send_message.assert_not_called()
