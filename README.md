# Ostium Python SDK

A python based SDK developed for interacting with Ostium v1 Trading Platform (https://ostium.app/)

Ostium is a decentralized perpetuals exchange on Arbitrum (Ethereum L2) with a focus on providing a seamless experience for traders for trading currencies, commodities, indices, crypto and more.

This SDK is designed to be used by developers who want to build applications on top of Ostium and automate their trading strategies.


## Installation

The SDK can be installed via pip:

```bash
pip install ostium-python-sdk
```

## Requirements

Developed using:
```python
  python=3.8
```
## SDK Instantiation 

You can instantiate the SDK with the following parameters. 
Ostium Platform is deployed on Arbitrum. You can use the testnet or mainnet config via the `NetworkConfig` class, see below for an example.

```python
from dotenv import load_dotenv
from ostium_python_sdk import OstiumSDK, NetworkConfig

# Load environment variables if using .env file
load_dotenv()

# Get private key from environment variable
private_key = os.getenv('PRIVATE_KEY')
if not private_key:
    raise ValueError("PRIVATE_KEY not found in .env file")

rpc_url = os.getenv('RPC_URL')
if not rpc_url:
    raise ValueError("RPC_URL not found in .env file")

# Initialize SDK
configTestnet = NetworkConfig.testnet()
configMainnet = NetworkConfig.mainnet()
sdk = OstiumSDK(configTestnet, private_key)
sdk = OstiumSDK(configMainnet, private_key)
```
<b>NOTE:</b> create a .env file with PRIVATE_KEY and RPC_URL to use the SDK. An RPC URL is required to use the SDK. You can get one by signing up for a free account at https://www.alchemy.com/ and creating an app. 

```
PRIVATE_KEY=your_private_key_here
RPC_URL=https://arb-sepolia.g.alchemy.com/v2/...
#RPC_URL="https://arb-mainnet.g.alchemy.com/v2/...",
```

`your_private_key_here` should be a valid EVM private key for an account on either Arbitrum (mainnet) or Arbitrum Sepolia (testnet), depending on which network you plan to use. Make sure to save it in a secure location, and that the .env file is not shared with anyone or committed to a public repository (make sure you add it to .gitignore if you are pushing your code).


## The SDK contains the following classes:

- `OstiumSDK`: The main class for interacting with the Ostium Platform.

- `NetworkConfig`: The class for configuring the network.

- `Balance`: The class for interacting with the account, fetching balance, etc. available via `sdk.balance`.

- `SubgraphClient`: The class for interacting with the subgraph, getting pair details, open trades, open orders,etc. available via `sdk.subgraph`.

- `Price`: The class for interacting with the price, fetching latest price, etc. available via `sdk.price`

- `Ostium`: The class for interacting with the Ostium Smart contracts, opening trades, updating take profit and stop loss, closing trades, opening orders, etc. available via `sdk.ostium`.

## Basic Usage

The intraction with Ostium platform is denoted with pair_id and trade_index. 

- `pair_id`: The id of the pair, available via `sdk.subgraph.get_pairs()`
- `trade_index`: The index of the trade for this trader on the pair, available via `sdk.subgraph.get_open_trades()`

## List of available pairs (Mainnet)

- As of January 2025, the following pairs are available on the mainnet: 

| ID | Trading Pair | Description                    |
|----|--------------|--------------------------------|
| 0  | BTC-USD      | Bitcoin                        |
| 1  | ETH-USD      | Ethereum                       |
| 2  | EUR-USD      | Euro                           |
| 3  | GBP-USD      | British Pound                  |
| 4  | USD-JPY      | US Dollar to Japanese Yen      |
| 5  | XAU-USD      | Gold                           |
| 6  | HG-USD       | Copper                         |
| 7  | CL-USD       | Crude Oil                      |
| 8  | XAG-USD      | Silver                         |
| 9  | SOL-USD      | Solana                         |
| 10 | SPX-USD      | S&P 500 Index                  |

## Usage Example

### Opening a Trade, Reading Open Trades, Setting Take Profit and Stop Loss, Closing a Trade

```python
from ostium_python_sdk import OstiumSDK
from dotenv import load_dotenv

# Load environment variables if using .env file
load_dotenv()

# Get private key from environment variable
private_key = os.getenv('PRIVATE_KEY')
if not private_key:
    raise ValueError("PRIVATE_KEY not found in .env file")

rpc_url = os.getenv('RPC_URL')
if not rpc_url:
    raise ValueError("RPC_URL not found in .env file")

# Initialize SDK
config = NetworkConfig.testnet()
sdk = OstiumSDK(config, private_key)

# Or initialize with explicit private key & rpc url
# sdk = OstiumSDK(
#     network="arbitrum",
#     private_key="your_private_key_here",
#     rpc_url="https://arb1.arbitrum.io/rpc"
# )

# Get all available pairs
pairs = await sdk.subgraph.get_pairs()

print("\nPair Information:")
print("----------------------------------------")

for pair in pairs:
    # Get detailed information for each pair from the Graph API
    pair_details = await sdk.subgraph.get_pair_details(pair['id'])
    print("\nPair Details:")
    print("----------------------------------------")
    # Print all available fields in pair_details
    for key, value in pair_details.items():
        print(f"{key}: {value}")
    print("----------------------------------------")


# Define trade parameters
trade_params = {
    'collateral': 100,        # USDC amount
    'leverage': 10,           # Leverage multiplier
    'asset_type': 0,          # 0 for BTC, see pair_details above for other asset types 
    'direction': True,        # True for Long, False for Short
    'order_type': 'MARKET'    # 'MARKET', 'LIMIT', or 'STOP'
}

try:
  # Get latest price for BTC
  latest_price, _ = await sdk.price.get_price("BTC", "USD")
  print(f"Latest price: {latest_price}")
  # Execute trade at current market price
  receipt = sdk.ostium.perform_trade(trade_params, at_price=latest_price)
  print(f"Trade successful! Transaction hash: {receipt['transactionHash'].hex()}")

  # Wait for the transaction to be confirmed
  await asyncio.sleep(10)

  # Get public address from private key
  account = Account.from_key(private_key)
  trader_public_address = account.address

  # Get the trade details
  open_trades = await sdk.subgraph.get_open_trades(trader_public_address)
  for trade_index, trade_data in enumerate(open_trades):
      print(f"Trade {trade_index + 1}: {trade_data}\n")

  if len(open_trades) == 0:
      print(
          "No open trades found. Maybe the trade failed? enough USDC and ETH in the account?")
  else:
      opened_trade = open_trades[len(open_trades) - 1]
      print(f"Opened trade: {opened_trade}\n")

      sdk.ostium.update_tp(
          opened_trade['pair']['id'], opened_trade['index'], latest_price * 1.02)
      print(f"Trade Take Profit set to 2% above the current price!\n")

      await asyncio.sleep(10)

      sdk.ostium.update_sl(
          opened_trade['pair']['id'], opened_trade['index'], latest_price * 0.99)
      print(f"Trade Stop Loss set to 1% below the current price!\n")

      await asyncio.sleep(10)

      receipt = sdk.ostium.close_trade(
          opened_trade['pair']['id'], opened_trade['index'])
      print(
          f"Closed trade! Transaction hash: {receipt['transactionHash'].hex()}\n")



except Exception as e:
  print(f"Trade failed: {str(e)}")

```

## Example Usage Scripts


### Read Block Number

To run the example:

```bash
python examples/example-read-block-number.py
```

See [example-read-block-number.py](https://github.com/0xOstium/ostium_python_sdk/blob/main/examples/example-read-block-number.py) for an example of how to use the SDK.

### Read Positions

To run the example:

```bash
python examples/example-read-positions.py
```

See [example-read-positions.py](https://github.com/0xOstium/ostium_python_sdk/blob/main/examples/example-read-positions.py) for an example of how to use the SDK.


### Get Feed Prices

To open a trade you need the latest feed price. 

See this example script on how to get the latest feed prices.

```bash
python examples/example-get-prices.py
```

See [example-get-prices.py](https://github.com/0xOstium/ostium_python_sdk/blob/main/examples/example-get-prices.py) for an example of how to use the SDK.



### Get Balance of an Address



See this example script on how to get the latest feed prices.

```bash
python examples/example-get-balance.py
```

See [example-get-balance.py](https://github.com/0xOstium/ostium_python_sdk/blob/main/examples/example-get-balance.py) for an example of how to use the SDK.




