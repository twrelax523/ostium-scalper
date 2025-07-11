# Changelog

All notable changes to the Ostium Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.18] - 2025-06-23

- Add delegate support for cancel_limit_order

## [2.0.17] - 2025-06-03

- Return target_funding_rate from getPendingAccFundingFees() 

## [2.0.16] - 2025-05-31

- query optional different address in sdk.get_open_trade_metrics()

## [2.0.15] - 2025-05-28

- Updated Readme with list of pairs
- Add additional fields to get_open_trade_metrics: bid, mid, ask, status

## [2.0.12] - 2025-05-28

- return isDayTradingClosed in sdk.get_formatted_pairs_details()

## [2.0.11] - 2025-05-28

- improve sdk.get_formatted_pairs_details()

## [2.0.10] - 2025-05-27

- Add sdk.get_target_funding_rate() for pair
- Fix Liquidiation price calculation
- Fix Funding Fee rate calculation
- Add get_pair_overnight_max_leverage() for pair

## [2.0.5] - 2025-05-26

- Support new ABIs from smart-contracts v.1.2.3: PairInfo, PairStorage, Trading, TradingStorage, Vault.
- Fix getTradeLiquidationPrice() exposed in sdk.get_open_trade_metrics()
- Allow get_open_trades() with an optional parameter trader_address
- Add sdk.get_rollover_rate_for_pair_id()

## [2.0.4] - 2025-05-26

### Added
- `track_order_and_trade` that let's you track an order status until its processed.
- Added support for delegation which allows an approved
  address (delegate) to execute trades on behalf of another address (trader).

## [2.0.3] - 2025-03-06

### Added
- `close_trade` that allows a partial close

## [2.0.2] - 2025-03-06

### Added
- `remove_collateral`


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