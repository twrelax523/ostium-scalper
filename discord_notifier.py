#!/usr/bin/env python3
"""
Discord Notifier for Ostium Trading Bot
Sends trade notifications to a Discord channel
"""

import os
import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class DiscordNotifier:
    """Discord webhook notifier for trading bot"""
    
    def __init__(self, webhook_url: str):
        """Initialize Discord notifier with webhook URL"""
        self.webhook_url = webhook_url
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def send_notification(self, title: str, description: str, color: int = 0x00ff00, fields: Optional[list] = None):
        """Send a notification to Discord"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "Ostium Trading Bot"
            }
        }
        
        if fields:
            embed["fields"] = fields
        
        payload = {
            "embeds": [embed]
        }
        
        try:
            async with self.session.post(self.webhook_url, json=payload) as response:
                if response.status == 204:
                    logger.info(f"Discord notification sent: {title}")
                else:
                    logger.error(f"Failed to send Discord notification: {response.status}")
        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}")
    
    async def notify_trade_opened(self, trade_info: Dict):
        """Notify when a trade is opened"""
        fields = [
            {"name": "Symbol", "value": trade_info.get('symbol', 'N/A'), "inline": True},
            {"name": "Side", "value": trade_info.get('side', 'N/A'), "inline": True},
            {"name": "Position Size", "value": f"${trade_info.get('position_size', 0):.2f}", "inline": True},
            {"name": "Entry Price", "value": f"${trade_info.get('entry_price', 0):.5f}", "inline": True},
            {"name": "Leverage", "value": f"{trade_info.get('leverage', 0)}x", "inline": True},
            {"name": "Transaction", "value": trade_info.get('transaction_hash', 'N/A')[:10] + "...", "inline": True}
        ]
        
        if trade_info.get('stop_loss'):
            fields.append({"name": "Stop Loss", "value": f"${trade_info['stop_loss']:.5f}", "inline": True})
        
        if trade_info.get('take_profit'):
            fields.append({"name": "Take Profit", "value": f"${trade_info['take_profit']:.5f}", "inline": True})
        
        await self.send_notification(
            title="🟢 Trade Opened",
            description=f"New {trade_info.get('side', 'Unknown')} position opened",
            color=0x00ff00,
            fields=fields
        )
    
    async def notify_trade_closed(self, trade_info: Dict):
        """Notify when a trade is closed"""
        fields = [
            {"name": "Symbol", "value": trade_info.get('symbol', 'N/A'), "inline": True},
            {"name": "Side", "value": trade_info.get('side', 'N/A'), "inline": True},
            {"name": "Entry Price", "value": f"${trade_info.get('entry_price', 0):.5f}", "inline": True},
            {"name": "Exit Price", "value": f"${trade_info.get('exit_price', 0):.5f}", "inline": True},
            {"name": "P&L", "value": f"${trade_info.get('pnl', 0):.2f}", "inline": True},
            {"name": "P&L %", "value": f"{trade_info.get('pnl_percent', 0):.2f}%", "inline": True},
            {"name": "Transaction", "value": trade_info.get('transaction_hash', 'N/A')[:10] + "...", "inline": True}
        ]
        
        # Set color based on P&L
        color = 0x00ff00 if trade_info.get('pnl', 0) >= 0 else 0xff0000
        
        await self.send_notification(
            title="🔴 Trade Closed",
            description=f"Position closed with {'profit' if trade_info.get('pnl', 0) >= 0 else 'loss'}",
            color=color,
            fields=fields
        )
    
    async def notify_signal_received(self, signal_info: Dict):
        """Notify when a signal is received"""
        fields = [
            {"name": "Symbol", "value": signal_info.get('symbol', 'N/A'), "inline": True},
            {"name": "Signal ID", "value": signal_info.get('signal_id', 'N/A'), "inline": True},
            {"name": "Type", "value": signal_info.get('signal_type', 'N/A'), "inline": True},
            {"name": "Side", "value": signal_info.get('side', 'N/A'), "inline": True}
        ]
        
        if signal_info.get('position_size'):
            fields.append({"name": "Position Size", "value": f"${signal_info['position_size']:.2f}", "inline": True})
        
        if signal_info.get('entry_price'):
            fields.append({"name": "Entry Price", "value": f"${signal_info['entry_price']:.5f}", "inline": True})
        
        await self.send_notification(
            title="📡 Signal Received",
            description="New TradingView signal received",
            color=0x0099ff,
            fields=fields
        )
    
    async def notify_error(self, error_message: str, context: str = ""):
        """Notify when an error occurs"""
        fields = []
        if context:
            fields.append({"name": "Context", "value": context, "inline": False})
        
        await self.send_notification(
            title="❌ Error Occurred",
            description=error_message,
            color=0xff0000,
            fields=fields
        )
    
    async def notify_balance_update(self, balance_info: Dict):
        """Notify balance updates"""
        fields = [
            {"name": "Total Balance", "value": f"${balance_info.get('balance', 0):.2f}", "inline": True},
            {"name": "Available", "value": f"${balance_info.get('available', 0):.2f}", "inline": True},
            {"name": "In Positions", "value": f"${balance_info.get('in_positions', 0):.2f}", "inline": True}
        ]
        
        await self.send_notification(
            title="💰 Balance Update",
            description="Portfolio balance updated",
            color=0xffff00,
            fields=fields
        ) 