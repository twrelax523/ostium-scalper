#!/usr/bin/env python3
"""
Discord Bot for Ostium Trading Bot
Provides trading commands and notifications
"""

import os
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

# Import the trading bot components
from trading_bot import OstiumTradingBot, TradingViewSignalParser
from ostium_python_sdk.config import NetworkConfig

logger = logging.getLogger(__name__)

class TradingDiscordBot(commands.Bot):
    """Discord bot for Ostium trading commands"""
    
    def __init__(self, trading_bot: OstiumTradingBot, discord_token: str):
        """Initialize Discord bot with trading bot instance"""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        super().__init__(command_prefix="!", intents=intents)
        self.trading_bot = trading_bot
        self.discord_token = discord_token
        
        # Register commands
        self.setup_commands()
    
    def setup_commands(self):
        """Setup slash commands"""
        
        @self.tree.command(name="portfolio", description="Get current portfolio balance")
        async def portfolio(interaction: discord.Interaction):
            await self.handle_portfolio(interaction)
        
        @self.tree.command(name="positions", description="Get current open positions")
        async def positions(interaction: discord.Interaction):
            await self.handle_positions(interaction)
        
        @self.tree.command(name="history", description="Get trading history")
        async def history(interaction: discord.Interaction):
            await self.handle_history(interaction)
        
        @self.tree.command(name="closetrade", description="Close a specific trade")
        async def closetrade(interaction: discord.Interaction, trade_id: str):
            await self.handle_closetrade(interaction, trade_id)
        
        @self.tree.command(name="trades", description="List all open trades with IDs")
        async def trades(interaction: discord.Interaction):
            await self.handle_trades(interaction)
    
    async def handle_portfolio(self, interaction: discord.Interaction):
        """Handle /portfolio command"""
        try:
            await interaction.response.defer()
            
            # Get balance
            balance = await self.trading_bot.sdk.balance.get_balance()
            
            # Get open positions to calculate total value
            open_positions = await self.trading_bot.get_open_positions()
            
            total_in_positions = 0
            for position in open_positions:
                total_in_positions += float(position.get('collateral', 0))
            
            embed = discord.Embed(
                title="💰 Portfolio Balance",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="Total Balance",
                value=f"${float(balance.get('balance', 0)):.2f}",
                inline=True
            )
            
            embed.add_field(
                name="Available",
                value=f"${float(balance.get('balance', 0)) - total_in_positions:.2f}",
                inline=True
            )
            
            embed.add_field(
                name="In Positions",
                value=f"${total_in_positions:.2f}",
                inline=True
            )
            
            embed.add_field(
                name="Open Positions",
                value=str(len(open_positions)),
                inline=True
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in portfolio command: {e}")
            await interaction.followup.send(f"❌ Error getting portfolio: {str(e)}")
    
    async def handle_positions(self, interaction: discord.Interaction):
        """Handle /positions command"""
        try:
            await interaction.response.defer()
            
            open_positions = await self.trading_bot.get_open_positions()
            
            if not open_positions:
                embed = discord.Embed(
                    title="📊 Open Positions",
                    description="No open positions found",
                    color=0xffff00,
                    timestamp=datetime.utcnow()
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="📊 Open Positions",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            for i, position in enumerate(open_positions[:10]):  # Limit to 10 positions
                pair_name = f"{position['pair']['from']}/{position['pair']['to']}"
                side = "LONG" if position.get('isBuy', True) else "SHORT"
                
                # Get position metrics if available
                try:
                    metrics = await self.trading_bot.sdk.get_open_trade_metrics(
                        position['pair']['id'],
                        position['index']
                    )
                    
                    pnl = metrics.get('unrealizedPnl', 0)
                    pnl_percent = metrics.get('profitPercent', 0)
                    
                    value = f"${pnl:.2f} ({pnl_percent:.2f}%)"
                    color = 0x00ff00 if pnl >= 0 else 0xff0000
                    
                except Exception:
                    value = "N/A"
                    color = 0x808080
                
                embed.add_field(
                    name=f"{i+1}. {pair_name} {side}",
                    value=f"Size: ${float(position.get('collateral', 0)):.2f}\n"
                          f"Leverage: {float(position.get('leverage', 0)):.1f}x\n"
                          f"Entry: ${float(position.get('openPrice', 0)):.5f}\n"
                          f"P&L: {value}",
                    inline=True
                )
            
            if len(open_positions) > 10:
                embed.set_footer(text=f"Showing 10 of {len(open_positions)} positions")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in positions command: {e}")
            await interaction.followup.send(f"❌ Error getting positions: {str(e)}")
    
    async def handle_history(self, interaction: discord.Interaction):
        """Handle /history command"""
        try:
            await interaction.response.defer()
            
            # Get recent history
            trader_address = self.trading_bot.sdk.ostium.get_public_address()
            history = await self.trading_bot.sdk.subgraph.get_recent_history(trader_address, last_n_orders=10)
            
            if not history:
                embed = discord.Embed(
                    title="📈 Trading History",
                    description="No recent trades found",
                    color=0xffff00,
                    timestamp=datetime.utcnow()
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="📈 Recent Trading History",
                color=0x0099ff,
                timestamp=datetime.utcnow()
            )
            
            for i, trade in enumerate(history[:5]):  # Limit to 5 recent trades
                pair_name = f"{trade['pair']['from']}/{trade['pair']['to']}"
                side = "LONG" if trade.get('isBuy', True) else "SHORT"
                status = "OPEN" if trade.get('isOpen', True) else "CLOSED"
                
                # Calculate P&L if closed
                pnl_info = ""
                if not trade.get('isOpen', True) and 'closePrice' in trade:
                    entry_price = float(trade.get('openPrice', 0))
                    exit_price = float(trade.get('closePrice', 0))
                    
                    if side == "LONG":
                        pnl_percent = ((exit_price - entry_price) / entry_price) * 100
                    else:
                        pnl_percent = ((entry_price - exit_price) / entry_price) * 100
                    
                    pnl_info = f"P&L: {pnl_percent:.2f}%"
                
                embed.add_field(
                    name=f"{i+1}. {pair_name} {side} ({status})",
                    value=f"Size: ${float(trade.get('collateral', 0)):.2f}\n"
                          f"Entry: ${float(trade.get('openPrice', 0)):.5f}\n"
                          f"{pnl_info}",
                    inline=True
                )
            
            if len(history) > 5:
                embed.set_footer(text=f"Showing 5 of {len(history)} recent trades")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in history command: {e}")
            await interaction.followup.send(f"❌ Error getting history: {str(e)}")
    
    async def handle_trades(self, interaction: discord.Interaction):
        """Handle /trades command - show all trades with IDs for closing"""
        try:
            await interaction.response.defer()
            
            open_positions = await self.trading_bot.get_open_positions()
            
            if not open_positions:
                embed = discord.Embed(
                    title="🔧 Available Trades to Close",
                    description="No open positions found",
                    color=0xffff00,
                    timestamp=datetime.utcnow()
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="🔧 Available Trades to Close",
                description="Use `/closetrade <trade_id>` to close a specific trade",
                color=0xff9900,
                timestamp=datetime.utcnow()
            )
            
            for i, position in enumerate(open_positions):
                pair_name = f"{position['pair']['from']}/{position['pair']['to']}"
                side = "LONG" if position.get('isBuy', True) else "SHORT"
                trade_id = f"{position['pair']['id']}_{position['index']}"
                
                embed.add_field(
                    name=f"Trade ID: `{trade_id}`",
                    value=f"Pair: {pair_name}\n"
                          f"Side: {side}\n"
                          f"Size: ${float(position.get('collateral', 0)):.2f}\n"
                          f"Entry: ${float(position.get('openPrice', 0)):.5f}",
                    inline=True
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in trades command: {e}")
            await interaction.followup.send(f"❌ Error getting trades: {str(e)}")
    
    async def handle_closetrade(self, interaction: discord.Interaction, trade_id: str):
        """Handle /closetrade command"""
        try:
            await interaction.response.defer()
            
            # Parse trade_id (format: pair_id_index)
            if '_' not in trade_id:
                await interaction.followup.send("❌ Invalid trade ID format. Use: pair_id_index (e.g., 1_0)")
                return
            
            pair_id, trade_index = trade_id.split('_')
            
            # Validate the trade exists
            open_positions = await self.trading_bot.get_open_positions()
            trade_exists = False
            
            for position in open_positions:
                if (str(position['pair']['id']) == pair_id and 
                    str(position['index']) == trade_index):
                    trade_exists = True
                    break
            
            if not trade_exists:
                await interaction.followup.send("❌ Trade not found or already closed")
                return
            
            # Close the trade
            close_result = self.trading_bot.sdk.ostium.close_trade(int(pair_id), int(trade_index))
            
            if close_result:
                embed = discord.Embed(
                    title="🔴 Trade Closed",
                    description=f"Successfully closed trade {trade_id}",
                    color=0xff0000,
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="Transaction Hash",
                    value=close_result['receipt']['transactionHash'].hex()[:20] + "...",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("❌ Failed to close trade")
            
        except Exception as e:
            logger.error(f"Error in closetrade command: {e}")
            await interaction.followup.send(f"❌ Error closing trade: {str(e)}")
    
    async def setup_hook(self):
        """Setup hook for Discord bot"""
        await self.tree.sync()
        logger.info("Discord bot commands synced")
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"Discord bot logged in as {self.user}")
        await self.change_presence(activity=discord.Game(name="Trading on Ostium"))

async def run_discord_bot(trading_bot: OstiumTradingBot, discord_token: str):
    """Run the Discord bot"""
    bot = TradingDiscordBot(trading_bot, discord_token)
    
    try:
        await bot.start(discord_token)
    except Exception as e:
        logger.error(f"Discord bot error: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    # This would be run separately from the main trading bot
    import asyncio
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Get configuration
    private_key = os.getenv('PRIVATE_KEY')
    rpc_url = os.getenv('RPC_URL')
    network_type = os.getenv('NETWORK_TYPE', 'testnet')
    discord_token = os.getenv('DISCORD_BOT_TOKEN')
    
    if not discord_token:
        print("DISCORD_BOT_TOKEN not found in environment variables")
        exit(1)
    
    # Initialize trading bot
    if network_type == 'mainnet':
        network_config = NetworkConfig.mainnet()
    else:
        network_config = NetworkConfig.testnet()
    
    trading_bot = OstiumTradingBot(network_config, private_key, rpc_url)
    
    # Run Discord bot
    asyncio.run(run_discord_bot(trading_bot, discord_token)) 