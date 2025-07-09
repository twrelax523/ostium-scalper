#!/usr/bin/env python3
"""
Gateway Discord Bot for Ostium Trading Bot
Connects to Discord Gateway to appear online and handle slash commands
"""

import os
import asyncio
import aiohttp
import logging
import json
import websockets
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class GatewayDiscordBot:
    """Discord bot using Gateway connection"""
    
    def __init__(self, trading_bot, discord_token: str):
        """Initialize Gateway Discord bot"""
        self.trading_bot = trading_bot
        self.discord_token = discord_token
        self.base_url = "https://discord.com/api/v10"
        self.gateway_url = "wss://gateway.discord.gg/?v=10&encoding=json"
        self.session = None
        self.ws = None
        self.heartbeat_interval = None
        self.sequence = None
        self.bot_id = None
        logger.info("Gateway Discord bot initialized")
    
    async def connect_gateway(self):
        """Connect to Discord Gateway"""
        try:
            # Get Gateway URL
            async with self.session.get(f"{self.base_url}/gateway/bot") as response:
                if response.status == 200:
                    gateway_info = await response.json()
                    self.gateway_url = gateway_info['url'] + "?v=10&encoding=json"
                else:
                    logger.error(f"Failed to get Gateway URL: {response.status}")
                    return False
            
            # Connect to Gateway
            self.ws = await websockets.connect(self.gateway_url)
            logger.info("Connected to Discord Gateway")
            
            # Send identify payload
            identify_payload = {
                "op": 2,
                "d": {
                    "token": self.discord_token,
                    "intents": 32768,  # Message content intent
                    "properties": {
                        "os": "linux",
                        "browser": "Ostium Trading Bot",
                        "device": "Ostium Trading Bot"
                    }
                }
            }
            
            await self.ws.send(json.dumps(identify_payload))
            logger.info("Sent identify payload")
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to Gateway: {e}")
            return False
    
    async def handle_gateway_message(self, message):
        """Handle incoming Gateway messages"""
        try:
            data = json.loads(message)
            op = data.get('op')
            
            if op == 10:  # Hello
                self.heartbeat_interval = data['d']['heartbeat_interval'] / 1000
                asyncio.create_task(self.heartbeat_loop())
                logger.info("Started heartbeat loop")
                
            elif op == 0:  # Dispatch
                event_type = data.get('t')
                self.sequence = data.get('s')
                
                if event_type == 'READY':
                    self.bot_id = data['d']['user']['id']
                    logger.info(f"Bot ready: {data['d']['user']['username']}")
                    
                elif event_type == 'INTERACTION_CREATE':
                    await self.handle_interaction(data['d'])
                    
        except Exception as e:
            logger.error(f"Error handling Gateway message: {e}")
    
    async def heartbeat_loop(self):
        """Send heartbeat to keep connection alive"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                heartbeat_payload = {
                    "op": 1,
                    "d": self.sequence
                }
                await self.ws.send(json.dumps(heartbeat_payload))
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break
    
    async def handle_interaction(self, interaction):
        """Handle slash command interactions"""
        try:
            command_name = interaction['data']['name']
            channel_id = interaction['channel_id']
            
            if command_name == 'portfolio':
                await self.handle_portfolio_command(channel_id)
            elif command_name == 'positions':
                await self.handle_positions_command(channel_id)
            else:
                await self.send_interaction_response(interaction, f"Unknown command: {command_name}")
                
        except Exception as e:
            logger.error(f"Error handling interaction: {e}")
            await self.send_interaction_response(interaction, f"Error: {str(e)}")
    
    async def send_interaction_response(self, interaction, content: str, embed: Optional[Dict] = None):
        """Send response to slash command interaction"""
        try:
            response_data = {
                "type": 4,  # Channel message with source
                "data": {
                    "content": content
                }
            }
            
            if embed:
                response_data["data"]["embeds"] = [embed]
            
            async with self.session.post(
                f"{self.base_url}/interactions/{interaction['id']}/{interaction['token']}/callback",
                json=response_data
            ) as response:
                if response.status != 204:
                    logger.error(f"Failed to send interaction response: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error sending interaction response: {e}")
    
    async def send_message(self, channel_id: str, content: str, embed: Optional[Dict] = None):
        """Send a message to a Discord channel"""
        if not self.session:
            return False
        
        payload = {"content": content}
        if embed:
            payload["embeds"] = [embed]
        
        try:
            async with self.session.post(
                f"{self.base_url}/channels/{channel_id}/messages",
                headers={
                    "Authorization": f"Bot {self.discord_token}",
                    "Content-Type": "application/json"
                },
                json=payload
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Error sending Discord message: {e}")
            return False
    
    def create_embed(self, title: str, description: str, color: int = 0x0099ff, fields: Optional[list] = None) -> Dict:
        """Create Discord embed"""
        embed = {
            'title': title,
            'description': description,
            'color': color,
            'timestamp': datetime.utcnow().isoformat(),
            'footer': {
                'text': 'Ostium Trading Bot'
            }
        }
        
        if fields:
            embed['fields'] = fields
        
        return embed
    
    async def handle_portfolio_command(self, channel_id: str):
        """Handle portfolio command"""
        try:
            # Get balance
            balance = await self.trading_bot.sdk.balance.get_balance()
            
            # Get open positions
            open_positions = await self.trading_bot.get_open_positions()
            
            total_in_positions = 0
            for position in open_positions:
                total_in_positions += float(position.get('collateral', 0))
            
            fields = [
                {
                    'name': 'Total Balance',
                    'value': f"${float(balance.get('balance', 0)):.2f}",
                    'inline': True
                },
                {
                    'name': 'Available',
                    'value': f"${float(balance.get('balance', 0)) - total_in_positions:.2f}",
                    'inline': True
                },
                {
                    'name': 'In Positions',
                    'value': f"${total_in_positions:.2f}",
                    'inline': True
                },
                {
                    'name': 'Open Positions',
                    'value': str(len(open_positions)),
                    'inline': True
                }
            ]
            
            embed = self.create_embed(
                title="💰 Portfolio Balance",
                description="Current portfolio status",
                color=0x00ff00,
                fields=fields
            )
            
            await self.send_message(channel_id, "", embed)
            
        except Exception as e:
            logger.error(f"Error in portfolio command: {e}")
            await self.send_message(channel_id, f"❌ Error getting portfolio: {str(e)}")
    
    async def handle_positions_command(self, channel_id: str):
        """Handle positions command"""
        try:
            open_positions = await self.trading_bot.get_open_positions()
            
            if not open_positions:
                embed = self.create_embed(
                    title="📊 Open Positions",
                    description="No open positions found",
                    color=0xffff00
                )
                await self.send_message(channel_id, "", embed)
                return
            
            # Create embed with positions
            embed = self.create_embed(
                title="📊 Open Positions",
                description=f"Found {len(open_positions)} open positions",
                color=0x00ff00
            )
            
            # Add position fields (limit to 10)
            for i, position in enumerate(open_positions[:10]):
                pair_name = f"{position['pair']['from']}/{position['pair']['to']}"
                side = "LONG" if position.get('isBuy', True) else "SHORT"
                
                embed['fields'].append({
                    'name': f"{i+1}. {pair_name} {side}",
                    'value': f"Size: ${float(position.get('collateral', 0)):.2f}\n"
                             f"Leverage: {float(position.get('leverage', 0)):.1f}x\n"
                             f"Entry: ${float(position.get('openPrice', 0)):.5f}",
                    'inline': True
                })
            
            if len(open_positions) > 10:
                embed['footer']['text'] = f"Showing 10 of {len(open_positions)} positions"
            
            await self.send_message(channel_id, "", embed)
            
        except Exception as e:
            logger.error(f"Error in positions command: {e}")
            await self.send_message(channel_id, f"❌ Error getting positions: {str(e)}")
    
    async def start(self):
        """Start the Discord bot"""
        try:
            self.session = aiohttp.ClientSession()
            
            # Connect to Gateway
            if not await self.connect_gateway():
                return
            
            # Listen for messages
            async for message in self.ws:
                await self.handle_gateway_message(message)
                
        except Exception as e:
            logger.error(f"Discord bot error: {e}")
        finally:
            if self.ws:
                await self.ws.close()
            if self.session:
                await self.session.close()

async def run_gateway_discord_bot(trading_bot, discord_token: str):
    """Run the Gateway Discord bot"""
    bot = GatewayDiscordBot(trading_bot, discord_token)
    await bot.start() 