#!/usr/bin/env python3
"""
Heroku Discord Bot Test
Script to test Discord bot token and diagnose issues on Heroku
"""

import os
import asyncio
import aiohttp
import json
import websockets
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_discord_token():
    """Test the Discord bot token"""
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("❌ DISCORD_BOT_TOKEN not found in environment variables")
        return False
    
    print(f"🔍 Testing Discord token: {token[:10]}...{token[-10:]}")
    
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bot {token}"}
        
        try:
            # Test 1: Get bot information
            async with session.get("https://discord.com/api/v10/users/@me", headers=headers) as response:
                print(f"📡 Bot info response: {response.status}")
                
                if response.status == 200:
                    bot_info = await response.json()
                    print(f"✅ Bot token is valid!")
                    print(f"🤖 Bot name: {bot_info.get('username', 'Unknown')}")
                    print(f"🆔 Bot ID: {bot_info.get('id', 'Unknown')}")
                    
                    # Generate invite link
                    bot_id = bot_info.get('id')
                    if bot_id:
                        permissions = "2147483648"
                        scopes = "bot%20applications.commands"
                        invite_link = f"https://discord.com/api/oauth2/authorize?client_id={bot_id}&permissions={permissions}&scope={scopes}"
                        print(f"🔗 Invite Link: {invite_link}")
                    
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Bot token is invalid: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error testing bot token: {e}")
            return False

async def test_gateway_connection():
    """Test Gateway connection"""
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("❌ DISCORD_BOT_TOKEN not found")
        return False
    
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bot {token}"}
        
        try:
            async with session.get("https://discord.com/api/v10/gateway/bot", headers=headers) as response:
                print(f"📡 Gateway response: {response.status}")
                
                if response.status == 200:
                    gateway_info = await response.json()
                    print(f"✅ Gateway connection successful!")
                    print(f"🌐 Gateway URL: {gateway_info.get('url', 'Unknown')}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Gateway connection failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error testing Gateway: {e}")
            return False

async def test_websocket_connection():
    """Test actual websocket connection"""
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("❌ DISCORD_BOT_TOKEN not found")
        return False
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bot {token}"}
            
            # Get Gateway URL
            async with session.get("https://discord.com/api/v10/gateway/bot", headers=headers) as response:
                if response.status == 200:
                    gateway_info = await response.json()
                    gateway_url = gateway_info['url'] + "?v=10&encoding=json"
                    print(f"🌐 Connecting to Gateway: {gateway_url}")
                    
                    # Connect to Gateway
                    ws = await websockets.connect(gateway_url)
                    print("✅ Connected to Discord Gateway")
                    
                    # Send identify payload
                    identify_payload = {
                        "op": 2,
                        "d": {
                            "token": token,
                            "intents": 32768,  # Message content intent
                            "properties": {
                                "os": "linux",
                                "browser": "Ostium Trading Bot",
                                "device": "Ostium Trading Bot"
                            }
                        }
                    }
                    
                    await ws.send(json.dumps(identify_payload))
                    print("✅ Sent identify payload")
                    
                    # Wait for response
                    response = await ws.recv()
                    response_data = json.loads(response)
                    
                    if response_data.get('op') == 0 and response_data.get('t') == 'READY':
                        bot_info = response_data['d']['user']
                        print(f"🎉 Bot successfully connected!")
                        print(f"🤖 Bot name: {bot_info.get('username', 'Unknown')}")
                        print(f"🆔 Bot ID: {bot_info.get('id', 'Unknown')}")
                        await ws.close()
                        return True
                    else:
                        print(f"❌ Unexpected response: {response_data}")
                        await ws.close()
                        return False
                        
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to get Gateway URL: {response.status} - {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error testing websocket connection: {e}")
        return False

async def check_environment():
    """Check environment variables"""
    print("🔧 Checking environment variables...")
    
    required_vars = [
        'DISCORD_BOT_TOKEN',
        'PRIVATE_KEY', 
        'RPC_URL',
        'NETWORK_TYPE'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * len(value)} (hidden)")
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("\n✅ All required environment variables are set")
        return True

async def main():
    """Main test function"""
    print("🧪 Heroku Discord Bot Diagnostics")
    print("=" * 50)
    
    # Check environment
    env_ok = await check_environment()
    print()
    
    if not env_ok:
        print("❌ Environment check failed. Please set missing variables.")
        return
    
    # Test 1: Token validity
    print("🔍 Testing Discord token...")
    token_valid = await test_discord_token()
    print()
    
    if not token_valid:
        print("❌ Token test failed. Please check your DISCORD_BOT_TOKEN.")
        return
    
    # Test 2: Gateway connection
    print("🌐 Testing Gateway connection...")
    gateway_valid = await test_gateway_connection()
    print()
    
    if not gateway_valid:
        print("❌ Gateway test failed.")
        return
    
    # Test 3: Websocket connection
    print("🔌 Testing websocket connection...")
    websocket_valid = await test_websocket_connection()
    print()
    
    if websocket_valid:
        print("✅ All tests passed! Bot should be able to connect.")
        print("\n💡 If the bot still appears offline:")
        print("1. Make sure the bot is invited to your server")
        print("2. Check that the bot has the right permissions")
        print("3. Verify the bot is not being rate limited")
    else:
        print("❌ Websocket test failed. Check the logs above for details.")
    
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main()) 