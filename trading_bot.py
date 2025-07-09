#!/usr/bin/env python3
"""
Ostium Trading Bot - TradingView Webhook Integration

This bot receives TradingView webhook signals and executes trades on the Ostium decentralized exchange.
It handles position opening, closing, and management based on incoming signals.

Signal Format Examples:
1. Market Entry Signal:
   "OANDA:EURUSD m10/m1
    HTF-LTF Long (Old Pivot/MS)
    ID: L23877
    Timeframe: m10 / m1
    Side: Long
    Type: Market
    Position Size $: 96081.748528
    Position Size (units): 82118.345123
    Trade Risk %: 0.06
    Entry Price: 1.17004
    Stop Loss: 1.16937
    Portfolio Value $: 8734.704412
    Net Capital $: 8734.704412"

2. Exit Signal:
   "OANDA:EURUSD m10/m1
    Fluid Exit (Opposite Setup)
    ID: L23877
    Timeframe: m10 / m1
    Price: 1.17086
    Portfolio Value: 8802.04145
    Net Capital: 8802.04145
    Net Profit %: 0.77
    Units Exited: 82118.3451230201
    Trade Status: Exited"
"""

import os
import sys
import asyncio
import json
import logging
import re
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from ostium_python_sdk import OstiumSDK
from ostium_python_sdk.config import NetworkConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    """Data class to hold parsed trading signal information"""
    symbol: str
    signal_id: str
    timeframe: str
    side: Optional[str] = None  # Long/Short
    order_type: Optional[str] = None  # Market/Limit/Stop
    position_size_usd: Optional[float] = None
    position_size_units: Optional[float] = None
    trade_risk_percent: Optional[float] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    portfolio_value: Optional[float] = None
    net_capital: Optional[float] = None
    current_price: Optional[float] = None
    net_profit_percent: Optional[float] = None
    units_exited: Optional[float] = None
    trade_status: Optional[str] = None
    is_exit_signal: bool = False

class TradingViewSignalParser:
    """Parser for TradingView webhook signals"""
    
    @staticmethod
    def parse_signal(signal_text: str) -> TradingSignal:
        """Parse TradingView signal text into structured data"""
        lines = signal_text.strip().split('\n')
        
        # Initialize signal with basic info
        signal = TradingSignal(
            symbol="",
            signal_id="",
            timeframe=""
        )
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Parse symbol and timeframe
            if ':' in line and '/' in line:
                parts = line.split(' ')
                if len(parts) >= 2:
                    # Extract EURUSD from OANDA:EURUSD
                    if ':' in parts[0]:
                        signal.symbol = parts[0].split(':')[1]
                    else:
                        signal.symbol = parts[0]
                    signal.timeframe = ' '.join(parts[1:])
            
            # Parse signal ID
            elif line.startswith('ID:'):
                signal.signal_id = line.split('ID:')[1].strip()
            
            # Parse side (Long/Short)
            elif line.startswith('Side:'):
                signal.side = line.split('Side:')[1].strip()
            
            # Parse order type
            elif line.startswith('Type:'):
                signal.order_type = line.split('Type:')[1].strip()
            
            # Parse position size in USD
            elif 'Position Size $:' in line:
                try:
                    signal.position_size_usd = float(line.split('Position Size $:')[1].strip())
                except ValueError:
                    pass
            
            # Parse position size in units
            elif 'Position Size (units):' in line:
                try:
                    signal.position_size_units = float(line.split('Position Size (units):')[1].strip())
                except ValueError:
                    pass
            
            # Parse trade risk percentage
            elif 'Trade Risk %:' in line:
                try:
                    signal.trade_risk_percent = float(line.split('Trade Risk %:')[1].strip())
                except ValueError:
                    pass
            
            # Parse entry price
            elif line.startswith('Entry Price:'):
                try:
                    signal.entry_price = float(line.split('Entry Price:')[1].strip())
                except ValueError:
                    pass
            
            # Parse stop loss
            elif line.startswith('Stop Loss:'):
                try:
                    signal.stop_loss = float(line.split('Stop Loss:')[1].strip())
                except ValueError:
                    pass
            
            # Parse portfolio value
            elif 'Portfolio Value $:' in line:
                try:
                    signal.portfolio_value = float(line.split('Portfolio Value $:')[1].strip())
                except ValueError:
                    pass
            elif line.startswith('Portfolio Value:'):
                try:
                    signal.portfolio_value = float(line.split('Portfolio Value:')[1].strip())
                except ValueError:
                    pass
            
            # Parse net capital
            elif 'Net Capital $:' in line:
                try:
                    signal.net_capital = float(line.split('Net Capital $:')[1].strip())
                except ValueError:
                    pass
            elif line.startswith('Net Capital:'):
                try:
                    signal.net_capital = float(line.split('Net Capital:')[1].strip())
                except ValueError:
                    pass
            
            # Parse current price (for exit signals)
            elif line.startswith('Price:'):
                try:
                    signal.current_price = float(line.split('Price:')[1].strip())
                except ValueError:
                    pass
            
            # Parse net profit percentage
            elif line.startswith('Net Profit %:'):
                try:
                    signal.net_profit_percent = float(line.split('Net Profit %:')[1].strip())
                except ValueError:
                    pass
            
            # Parse units exited
            elif line.startswith('Units Exited:'):
                try:
                    signal.units_exited = float(line.split('Units Exited:')[1].strip())
                except ValueError:
                    pass
            
            # Parse trade status
            elif line.startswith('Trade Status:'):
                signal.trade_status = line.split('Trade Status:')[1].strip()
                signal.is_exit_signal = signal.trade_status == 'Exited'
        
        return signal

class OstiumTradingBot:
    """Main trading bot class for Ostium integration"""
    
    def __init__(self, network_config: NetworkConfig, private_key: str, rpc_url: str):
        """Initialize the trading bot with Ostium SDK"""
        self.sdk = OstiumSDK(network_config, private_key, rpc_url, verbose=True)
        self.signal_parser = TradingViewSignalParser()
        
        # Trading configuration
        self.default_leverage = 10  # Default leverage (10x)
        self.max_leverage = 100     # Maximum leverage allowed
        self.min_collateral = 10    # Minimum collateral in USDC
        self.max_collateral = 10000 # Maximum collateral in USDC
        
        # Position tracking
        self.active_positions = {}  # Track active positions by signal_id
        
        logger.info("Trading bot initialized successfully")
    
    async def get_available_pairs(self) -> List[Dict]:
        """Get available trading pairs from Ostium"""
        try:
            pairs = await self.sdk.subgraph.get_pairs()
            logger.info(f"Found {len(pairs)} available pairs")
            return pairs
        except Exception as e:
            logger.error(f"Error fetching pairs: {e}")
            return []
    
    def find_pair_by_symbol(self, symbol: str, pairs: List[Dict]) -> Optional[Dict]:
        """Find Ostium pair by TradingView symbol"""
        # Map common symbols to Ostium pairs
        symbol_mapping = {
            'EURUSD': 'EUR/USD',
            'GBPUSD': 'GBP/USD',
            'USDJPY': 'USD/JPY',
            'USDCHF': 'USD/CHF',
            'AUDUSD': 'AUD/USD',
            'USDCAD': 'USD/CAD',
            'NZDUSD': 'NZD/USD',
            'BTCUSD': 'BTC/USD',
            'ETHUSD': 'ETH/USD',
            'BTCUSDT': 'BTC/USDT',
            'ETHUSDT': 'ETH/USDT'
        }
        
        target_pair = symbol_mapping.get(symbol, symbol)
        
        for pair in pairs:
            if f"{pair['from']}/{pair['to']}" == target_pair:
                return pair
        
        return None
    
    async def get_open_positions(self) -> List[Dict]:
        """Get current open positions"""
        try:
            open_trades, trader_address = await self.sdk.get_open_trades()
            logger.info(f"Found {len(open_trades)} open positions")
            return open_trades
        except Exception as e:
            logger.error(f"Error fetching open positions: {e}")
            return []
    
    def calculate_position_size(self, signal: TradingSignal, available_capital: float) -> float:
        """Calculate position size based on signal and available capital"""
        if signal.position_size_usd:
            # Use the position size from the signal
            return min(signal.position_size_usd, available_capital)
        elif signal.trade_risk_percent and signal.net_capital:
            # Calculate based on risk percentage
            risk_amount = (signal.trade_risk_percent / 100) * signal.net_capital
            return min(risk_amount, available_capital)
        else:
            # Default to a percentage of available capital
            return min(available_capital * 0.1, available_capital)  # 10% of capital
    
    async def execute_trade(self, signal: TradingSignal) -> Dict:
        """Execute a trade based on the signal"""
        try:
            # Get available pairs
            pairs = await self.get_available_pairs()
            if not pairs:
                raise Exception("No trading pairs available")
            
            # Find the matching pair
            pair = self.find_pair_by_symbol(signal.symbol, pairs)
            if not pair:
                raise Exception(f"No matching pair found for symbol {signal.symbol}")
            
            logger.info(f"Found pair: {pair['from']}/{pair['to']} (ID: {pair['id']})")
            
            # Get current balance
            balance = await self.sdk.balance.get_balance()
            available_capital = float(balance['balance']) if balance else 0
            
            logger.info(f"Available capital: ${available_capital:.2f}")
            
            if available_capital < self.min_collateral:
                raise Exception(f"Insufficient capital. Required: ${self.min_collateral}, Available: ${available_capital:.2f}")
            
            # Calculate position size
            position_size = self.calculate_position_size(signal, available_capital)
            
            # Determine trade direction
            is_long = signal.side.lower() == 'long'
            
            # Get current price
            current_price, _, _ = await self.sdk.price.get_price(signal.symbol[:3], signal.symbol[3:])
            
            # Prepare trade parameters
            trade_params = {
                'collateral': position_size,
                'leverage': self.default_leverage,
                'asset_type': int(pair['id']),
                'direction': is_long,
                'order_type': 'MARKET'
            }
            
            # Add stop loss if provided
            if signal.stop_loss:
                trade_params['sl'] = signal.stop_loss
            
            # Add take profit if provided (you can calculate this based on risk/reward ratio)
            if signal.entry_price and signal.stop_loss:
                # Calculate take profit based on 1:2 risk/reward ratio
                if is_long:
                    price_diff = signal.entry_price - signal.stop_loss
                    take_profit = signal.entry_price + (price_diff * 2)
                else:
                    price_diff = signal.stop_loss - signal.entry_price
                    take_profit = signal.entry_price - (price_diff * 2)
                trade_params['tp'] = take_profit
            
            logger.info(f"Executing trade with params: {trade_params}")
            
            # Execute the trade
            trade_result = self.sdk.ostium.perform_trade(trade_params, at_price=current_price)
            
            # Store position information
            position_info = {
                'signal_id': signal.signal_id,
                'pair_id': pair['id'],
                'trade_index': 0,  # Will be updated after order tracking
                'side': signal.side,
                'entry_price': current_price,
                'position_size': position_size,
                'timestamp': datetime.now().isoformat()
            }
            
            # Track the order to get the trade index
            if trade_result.get('order_id'):
                order_result = await self.sdk.ostium.track_order_and_trade(
                    self.sdk.subgraph, 
                    trade_result['order_id']
                )
                
                if order_result.get('trade'):
                    trade = order_result['trade']
                    position_info['trade_index'] = trade.get('index', 0)
                    self.active_positions[signal.signal_id] = position_info
            
            logger.info(f"Trade executed successfully. Transaction: {trade_result['receipt']['transactionHash'].hex()}")
            
            return {
                'success': True,
                'transaction_hash': trade_result['receipt']['transactionHash'].hex(),
                'order_id': trade_result.get('order_id'),
                'position_info': position_info
            }
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def close_position(self, signal: TradingSignal) -> Dict:
        """Close an existing position"""
        try:
            # Find the position to close
            position = self.active_positions.get(signal.signal_id)
            if not position:
                # Try to find by symbol if signal_id doesn't match
                open_positions = await self.get_open_positions()
                matching_position = None
                
                for pos in open_positions:
                    pair_name = f"{pos['pair']['from']}/{pos['pair']['to']}"
                    if pair_name.replace('/', '') == signal.symbol:
                        matching_position = pos
                        break
                
                if not matching_position:
                    raise Exception(f"No active position found for signal {signal.signal_id}")
                
                position = {
                    'pair_id': matching_position['pair']['id'],
                    'trade_index': matching_position['index']
                }
            
            logger.info(f"Closing position: Pair {position['pair_id']}, Index {position['trade_index']}")
            
            # Close the position
            close_result = self.sdk.ostium.close_trade(
                position['pair_id'], 
                position['trade_index']
            )
            
            # Track the close order
            if close_result.get('order_id'):
                order_result = await self.sdk.ostium.track_order_and_trade(
                    self.sdk.subgraph, 
                    close_result['order_id']
                )
            
            # Remove from active positions
            if signal.signal_id in self.active_positions:
                del self.active_positions[signal.signal_id]
            
            logger.info(f"Position closed successfully. Transaction: {close_result['receipt']['transactionHash'].hex()}")
            
            return {
                'success': True,
                'transaction_hash': close_result['receipt']['transactionHash'].hex(),
                'order_id': close_result.get('order_id')
            }
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def process_signal(self, signal_text: str) -> Dict:
        """Process a TradingView signal"""
        try:
            # Parse the signal
            signal = self.signal_parser.parse_signal(signal_text)
            logger.info(f"Parsed signal: {signal}")
            
            if not signal.symbol or not signal.signal_id:
                raise Exception("Invalid signal format: missing symbol or signal ID")
            
            # Handle exit signals
            if signal.is_exit_signal:
                logger.info("Processing exit signal")
                return await self.close_position(signal)
            
            # Handle entry signals
            if signal.side and signal.order_type:
                logger.info("Processing entry signal")
                return await self.execute_trade(signal)
            
            # Handle informational signals (no action needed)
            logger.info("Processing informational signal (no action required)")
            return {
                'success': True,
                'message': 'Informational signal processed (no action required)'
            }
            
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Flask app for webhook endpoint
app = Flask(__name__)

# Global bot instance
trading_bot = None
discord_notifier = None

@app.route('/webhook', methods=['POST'])
async def webhook_handler():
    """Handle incoming TradingView webhook signals"""
    try:
        # Get the signal data
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        # Extract signal text
        signal_text = data.get('signal', '')
        if not signal_text:
            return jsonify({'error': 'No signal text found'}), 400
        
        logger.info(f"Received signal: {signal_text}")
        
        # Notify Discord about signal received
        if discord_notifier:
            signal = trading_bot.signal_parser.parse_signal(signal_text)
            await discord_notifier.notify_signal_received({
                'symbol': signal.symbol,
                'signal_id': signal.signal_id,
                'signal_type': 'Exit' if signal.is_exit_signal else 'Entry',
                'side': signal.side,
                'position_size': signal.position_size_usd,
                'entry_price': signal.entry_price
            })
        
        # Process the signal
        result = await trading_bot.process_signal(signal_text)
        
        if result['success']:
            # Notify Discord about successful trade
            if discord_notifier and 'position_info' in result.get('result', {}):
                position_info = result['result']['position_info']
                if 'transaction_hash' in result.get('result', {}):
                    await discord_notifier.notify_trade_opened({
                        'symbol': position_info.get('symbol', 'Unknown'),
                        'side': position_info.get('side', 'Unknown'),
                        'position_size': position_info.get('position_size', 0),
                        'entry_price': position_info.get('entry_price', 0),
                        'leverage': trading_bot.default_leverage,
                        'transaction_hash': result['result']['transaction_hash'],
                        'stop_loss': position_info.get('stop_loss'),
                        'take_profit': position_info.get('take_profit')
                    })
            
            return jsonify({
                'success': True,
                'message': 'Signal processed successfully',
                'result': result
            })
        else:
            # Notify Discord about error
            if discord_notifier:
                await discord_notifier.notify_error(
                    result.get('error', 'Unknown error'),
                    'Signal Processing'
                )
            
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 500
            
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    discord_status = "enabled" if os.getenv('DISCORD_BOT_TOKEN') else "disabled"
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'discord_bot': discord_status
    })

@app.route('/positions', methods=['GET'])
async def get_positions():
    """Get current positions"""
    try:
        open_positions = await trading_bot.get_open_positions()
        return jsonify({
            'success': True,
            'positions': open_positions,
            'active_signals': trading_bot.active_positions
        })
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return jsonify({'error': str(e)}), 500

async def initialize_bot():
    """Initialize the trading bot"""
    global trading_bot, discord_notifier
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    private_key = os.getenv('PRIVATE_KEY')
    rpc_url = os.getenv('RPC_URL')
    network_type = os.getenv('NETWORK_TYPE', 'testnet')  # testnet or mainnet
    discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    if not private_key:
        raise ValueError("PRIVATE_KEY not found in environment variables")
    if not rpc_url:
        raise ValueError("RPC_URL not found in environment variables")
    
    # Initialize network config
    if network_type == 'mainnet':
        network_config = NetworkConfig.mainnet()
    else:
        network_config = NetworkConfig.testnet()
    
    # Initialize trading bot
    trading_bot = OstiumTradingBot(network_config, private_key, rpc_url)
    
    # Initialize Discord notifier if webhook URL is provided
    if discord_webhook_url:
        from discord_notifier import DiscordNotifier
        discord_notifier = DiscordNotifier(discord_webhook_url)
        logger.info("Discord notifier initialized")
    else:
        logger.warning("DISCORD_WEBHOOK_URL not provided - Discord notifications disabled")
    
    logger.info(f"Trading bot initialized for {network_type}")

def main():
    """Main function to run the trading bot"""
    logger.info("Starting trading bot application...")
    
    # Run the Flask app
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()

# Initialize the bot when the module is imported (for Heroku)
import threading

def start_bot_in_background():
    """Start the bot in a background thread"""
    try:
        asyncio.run(initialize_bot())
        
        # Start Discord bot in background if token is provided
        discord_token = os.getenv('DISCORD_BOT_TOKEN')
        logger.info(f"Discord token found: {'Yes' if discord_token else 'No'}")
        if discord_token:
            from discord_runner import run_discord_bot
            
            def run_discord():
                try:
                    logger.info("Starting Discord bot thread...")
                    asyncio.run(run_discord_bot(trading_bot, discord_token))
                except Exception as e:
                    logger.error(f"Discord bot thread error: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            discord_thread = threading.Thread(target=run_discord)
            discord_thread.daemon = True
            discord_thread.start()
            logger.info("Discord bot thread started in background")
        else:
            logger.warning("DISCORD_BOT_TOKEN not provided - Discord commands disabled")
            
    except Exception as e:
        logger.error(f"Error initializing bot: {e}")
        import traceback
        logger.error(traceback.format_exc())

# Start the bot in background thread
bot_thread = threading.Thread(target=start_bot_in_background)
bot_thread.daemon = True
bot_thread.start() 