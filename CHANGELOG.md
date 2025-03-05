# Changelog

All notable changes to the Ostium Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1] - 2025-03-05

### Added
- Validate RPC_URL given correspondes with mainnet/testnet


## [2.0.0] - 2025-03-04

Version 2.0

## [0.2.1] - 2025-02-21

### Added
- Added sdk method `get_pair_net_rate_percent_per_hours` to get net rate percent per hours for a given pair

## [0.2.0] - 2025-02-20

### Added

- Added sdk method `get_open_trade_metrics` to get open trade metrics such as:
  - Funding fee
  - Roll over fee
  - Unrealized Pnl and Pnl Percent
  - Total Profit
  - Liquidation Price 

- Added verbose mode to sdk (default is False, set to True to see debug logs)

## [0.1.36] - 2025-01-14

### Added
- Before write-operations, check if private key is provided

## [0.1.34] - 2025-01-14

### Added
- Allow read only operations on the SDK without providing a private key

## [0.1.31] - 2025-01-13

### Added
- Add `get_formatted_pairs_details` on sdk class

## [0.1.25] - 2025-01-13

### Added
- Custom slippage control functionality
  - New method `set_slippage_percentage()` to customize trade slippage
  - New method `get_slippage_percentage()` to check current slippage setting
  - Ability to set slippage beyond the default 2%
- add USDC faucet ability to sdk for testnet configuration
- Add trades history - `get_recent_history`
- Adding of Tests


## [0.1.0] - 2025-01-10

### Added
- Initial release of Ostium Python SDK
- Core trading functionality:
  - Market, limit, and stop orders
  - Position management (open, close, modify)
  - Take profit and stop loss settings
- Price feed integration
- Balance checking and management
- Testnet faucet integration
- Subgraph querying for market data
- Comprehensive documentation and examples 