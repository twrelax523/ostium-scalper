#!/usr/bin/env python3
"""
Discord Notifier for Ostium Trading Bot
Sends notifications to Discord via webhook
"""

import os
import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class DiscordNotifier:
    """Discord webhook notifier for trading bot"""
    
    def __init__(self, webhook_url: str):
        """Initialize Discord notifier with webhook URL"""
        self.webhook_url = webhook_url
        logger.info("Discord notifier initialized")
    
    async def send_webhook(self, embed_data: Dict) -> bool:
        """Send webhook to Discord"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json={'embeds': [embed_data]},
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 204:
                        logger.info("Discord notification sent successfully")
                        return True
                    else:
                        logger.error(f"Discord webhook failed: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error sending Discord webhook: {e}")
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
    
    async def notify_signal_received(self, signal_data: Dict):
        """Notify about received trading signal"""
        fields = [
            {
                'name': 'Symbol',
                'value': signal_data.get('symbol', 'Unknown'),
                'inline': True
            },
            {
                'name': 'Signal Type',
                'value': signal_data.get('signal_type', 'Unknown'),
                'inline': True
            },
            {
                'name': 'Side',
                'value': signal_data.get('side', 'Unknown'),
                'inline': True
            }
        ]
        
        if signal_data.get('position_size'):
            fields.append({
                'name': 'Position Size',
                'value': f"${signal_data['position_size']:.2f}",
                'inline': True
            })
        
        if signal_data.get('entry_price'):
            fields.append({
                'name': 'Entry Price',
                'value': f"${signal_data['entry_price']:.5f}",
                'inline': True
            })
        
        embed = self.create_embed(
            title="📊 Trading Signal Received",
            description=f"Processing signal {signal_data.get('signal_id', 'Unknown')}",
            color=0x0099ff,
            fields=fields
        )
        
        await self.send_webhook(embed)
    
    async def notify_trade_opened(self, trade_data: Dict):
        """Notify about opened trade"""
        fields = [
            {
                'name': 'Symbol',
                'value': trade_data.get('symbol', 'Unknown'),
                'inline': True
            },
            {
                'name': 'Side',
                'value': trade_data.get('side', 'Unknown'),
                'inline': True
            },
            {
                'name': 'Position Size',
                'value': f"${trade_data.get('position_size', 0):.2f}",
                'inline': True
            },
            {
                'name': 'Entry Price',
                'value': f"${trade_data.get('entry_price', 0):.5f}",
                'inline': True
            },
            {
                'name': 'Leverage',
                'value': f"{trade_data.get('leverage', 0)}x",
                'inline': True
            }
        ]
        
        if trade_data.get('stop_loss'):
            fields.append({
                'name': 'Stop Loss',
                'value': f"${trade_data['stop_loss']:.5f}",
                'inline': True
            })
        
        if trade_data.get('take_profit'):
            fields.append({
                'name': 'Take Profit',
                'value': f"${trade_data['take_profit']:.5f}",
                'inline': True
            })
        
        if trade_data.get('transaction_hash'):
            fields.append({
                'name': 'Transaction',
                'value': f"[View on Arbiscan](https://arbiscan.io/tx/{trade_data['transaction_hash']})",
                'inline': False
            })
        
        embed = self.create_embed(
            title="✅ Trade Opened",
            description="New position opened successfully",
            color=0x00ff00,
            fields=fields
        )
        
        await self.send_webhook(embed)
    
    async def notify_trade_closed(self, trade_data: Dict):
        """Notify about closed trade"""
        fields = [
            {
                'name': 'Symbol',
                'value': trade_data.get('symbol', 'Unknown'),
                'inline': True
            },
            {
                'name': 'Side',
                'value': trade_data.get('side', 'Unknown'),
                'inline': True
            },
            {
                'name': 'Exit Price',
                'value': f"${trade_data.get('exit_price', 0):.5f}",
                'inline': True
            }
        ]
        
        if trade_data.get('pnl'):
            pnl = trade_data['pnl']
            color = 0x00ff00 if pnl >= 0 else 0xff0000
            fields.append({
                'name': 'P&L',
                'value': f"${pnl:.2f}",
                'inline': True
            })
        else:
            color = 0x0099ff
        
        if trade_data.get('transaction_hash'):
            fields.append({
                'name': 'Transaction',
                'value': f"[View on Arbiscan](https://arbiscan.io/tx/{trade_data['transaction_hash']})",
                'inline': False
            })
        
        embed = self.create_embed(
            title="🔒 Trade Closed",
            description="Position closed successfully",
            color=color,
            fields=fields
        )
        
        await self.send_webhook(embed)
    
    async def notify_error(self, error_message: str, context: str = "Trading Bot"):
        """Notify about error"""
        embed = self.create_embed(
            title="❌ Error",
            description=f"**{context}**\n{error_message}",
            color=0xff0000
        )
        
        await self.send_webhook(embed)
    
    async def notify_balance_update(self, balance_data: Dict):
        """Notify about balance update"""
        fields = [
            {
                'name': 'Total Balance',
                'value': f"${balance_data.get('total_balance', 0):.2f}",
                'inline': True
            },
            {
                'name': 'Available',
                'value': f"${balance_data.get('available', 0):.2f}",
                'inline': True
            },
            {
                'name': 'In Positions',
                'value': f"${balance_data.get('in_positions', 0):.2f}",
                'inline': True
            }
        ]
        
        embed = self.create_embed(
            title="💰 Balance Update",
            description="Portfolio balance updated",
            color=0x0099ff,
            fields=fields
        )
        
        await self.send_webhook(embed) 