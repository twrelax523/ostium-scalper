#!/usr/bin/env python3
"""
Simple Discord Bot for Ostium Trading Bot
Uses Discord REST API directly without discord.py
"""

import os
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class SimpleDiscordBot:
    """Simple Discord bot using REST API"""
    
    def __init__(self, trading_bot, discord_token: str):
        """Initialize simple Discord bot"""
        self.trading_bot = trading_bot
        self.discord_token = discord_token
        self.base_url = "https://discord.com/api/v10"
        self.session = None
        logger.info("Simple Discord bot initialized")
    
    async def start(self):
        """Start the Discord bot"""
        try:
            self.session = aiohttp.ClientSession()
            
            # Get bot info
            async with self.session.get(
                f"{self.base_url}/users/@me",
                headers={"Authorization": f"Bot {self.discord_token}"}
            ) as response:
                if response.status == 200:
                    bot_info = await response.json()
                    logger.info(f"Discord bot connected: {bot_info.get('username', 'Unknown')}")
                else:
                    logger.error(f"Failed to connect to Discord: {response.status}")
                    return
            
            # Keep the bot running
            while True:
                await asyncio.sleep(60)  # Check every minute
                
        except Exception as e:
            logger.error(f"Discord bot error: {e}")
        finally:
            if self.session:
                await self.session.close()
    
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

async def run_simple_discord_bot(trading_bot, discord_token: str):
    """Run the simple Discord bot"""
    bot = SimpleDiscordBot(trading_bot, discord_token)
    await bot.start() 