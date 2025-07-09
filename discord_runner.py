#!/usr/bin/env python3
"""
Discord Bot Runner - Separate module to avoid circular imports
"""

import asyncio
import logging
from discord_bot import TradingDiscordBot

logger = logging.getLogger(__name__)

async def run_discord_bot(trading_bot, discord_token: str):
    """Run the Discord bot"""
    bot = TradingDiscordBot(trading_bot, discord_token)
    
    try:
        logger.info("Starting Discord bot...")
        await bot.start(discord_token)
    except Exception as e:
        logger.error(f"Discord bot error: {e}")
        # Retry after delay
        await asyncio.sleep(5)
        await run_discord_bot(trading_bot, discord_token)
    finally:
        try:
            await bot.close()
        except:
            pass 