"""
Local testing script for the HelloBot
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bot import local_handler
from discord_interactions import InteractionType

def test_ping():
    """Test PING interaction"""
    print("Testing PING interaction...")
    response = local_handler({'type': InteractionType.PING})
    print(f"Response: {response}")
    assert response['statusCode'] == 200
    print("✓ PING test passed\n")

def test_hellobot_command():
    """Test /hellobot command"""
    print("Testing /hellobot command...")
    response = local_handler({
        'type': InteractionType.APPLICATION_COMMAND,
        'data': {'name': 'hellobot'},
        'user': {'username': 'TestUser'}
    })
    print(f"Response: {response}")
    assert response['statusCode'] == 200
    assert 'Hello TestUser' in response['body']
    print("✓ /hellobot test passed\n")

def test_with_member():
    """Test with member object (guild context)"""
    print("Testing /hellobot with member context...")
    response = local_handler({
        'type': InteractionType.APPLICATION_COMMAND,
        'data': {'name': 'hellobot'},
        'member': {
            'user': {'username': 'GuildUser'}
        }
    })
    print(f"Response: {response}")
    assert response['statusCode'] == 200
    assert 'Hello GuildUser' in response['body']
    print("✓ Member context test passed\n")

if __name__ == '__main__':
    print("🧪 Running HelloBot local tests...\n")
    
    # Set dummy public key for testing
    os.environ['DISCORD_PUBLIC_KEY'] = 'test_key_for_local_testing'
    
    try:
        test_ping()
        test_hellobot_command()
        test_with_member()
        print("✅ All tests passed!")
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
