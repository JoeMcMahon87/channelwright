"""
Shared test fixtures
"""
import json
import os
import time

import pytest
from nacl.signing import SigningKey

# bot.py creates its SQS client at import time, which needs a region
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')

SIGNING_KEY = SigningKey.generate()
os.environ['DISCORD_PUBLIC_KEY'] = SIGNING_KEY.verify_key.encode().hex()
os.environ['DISCORD_BOT_TOKEN'] = 'test-bot-token'
os.environ['SQS_QUEUE_URL'] = 'https://sqs.us-east-1.amazonaws.com/123456789012/channelwright-tasks'


@pytest.fixture
def signed_event():
    """
    Build an API Gateway event signed the way Discord signs interactions
    """
    def _build(payload):
        body = json.dumps(payload)
        timestamp = str(int(time.time()))
        signature = SIGNING_KEY.sign(f"{timestamp}{body}".encode()).signature.hex()
        return {
            'headers': {
                'x-signature-ed25519': signature,
                'x-signature-timestamp': timestamp
            },
            'body': body
        }
    return _build
