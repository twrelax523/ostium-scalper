import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the parent directory to the Python path so we can import the local module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Now import from the local module
from ostium_python_sdk import OstiumSDK
from ostium_python_sdk.config import NetworkConfig


async def main():
    # Load environment variables
    load_dotenv()

    # Get private key and RPC URL from environment variables
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        raise ValueError("PRIVATE_KEY not found in .env file")

    rpc_url = os.getenv('RPC_URL')
    if not rpc_url:
        raise ValueError("RPC_URL not found in .env file")

    # Initialize with testnet config
    config = NetworkConfig.mainnet()
    # Or for mainnet:
    # config = NetworkConfig.mainnet()

    # Initialize SDK - use OstiumSDK instead of Ostium
    sdk = OstiumSDK(config, private_key, rpc_url, verbose=True)

    # Define trade parameters
    trade_params = {
        'collateral': 10,       # USDC amount
        'leverage': 100,          # Leverage multiplier
        'asset_type': 0,        # 0 for BTC, see pair_details in README for other asset types
        'direction': True,      # True for Long, False for Short
        'order_type': 'MARKET'  # 'MARKET', 'LIMIT', or 'STOP'
        # Optional: set take profit/stop loss
        # 'tp': 0,              # Take Profit price - if not specified or Zero means no TP
        # 'sl': 0,              # Stop Loss price - if not specified or Zero means no SL
    }

    try:
        # Set slippage percentage (default is 2%)
        sdk.ostium.set_slippage_percentage(1)
        print(f"Slippage percentage set to: {sdk.ostium.get_slippage_percentage()}%")

        # Get latest price for BTC
        latest_price, _, _ = await sdk.price.get_price("BTC", "USD")
        print(f"Latest BTC/USD price: ${latest_price:,.2f}")

        # Execute trade at current market price
        print("Placing market order...")
        trade_result = sdk.ostium.perform_trade(trade_params, at_price=latest_price)
        
        # Get transaction receipt and order ID
        receipt = trade_result['receipt']
        order_id = trade_result['order_id']
        
        print(f"Order successful!")
        print(f"Transaction hash: {receipt['transactionHash'].hex()}")
        print(f"Order ID: {order_id}")        

    except Exception as e:
        print(f"Error placing order: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main()) 