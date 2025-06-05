import os
import pytest
from decimal import Decimal
from dotenv import load_dotenv
from ostium_python_sdk import OstiumSDK
from ostium_python_sdk.config import NetworkConfig
from eth_account import Account


@pytest.fixture(scope="module")
def sdk():
    # Load environment variables
    load_dotenv()

    rpc_url = os.getenv('RPC_URL')
    if not rpc_url:
        raise ValueError("RPC_URL not found in .env file")

    # Initialize SDK with testnet config
    config = NetworkConfig.testnet()
    return OstiumSDK(config)


@pytest.fixture(scope="module")
def account():
    if not os.getenv('PRIVATE_KEY'):
        pytest.skip("PRIVATE_KEY not found in .env file")
    return Account.from_key(os.getenv('PRIVATE_KEY'))


def test_convert_to_shares(sdk):
    """Test converting assets to shares"""
    # Test with 1000 USDC
    assets = Decimal('1000.0')
    shares = sdk.vault.convert_to_shares(assets)

    # Shares should be greater than 0
    assert shares > 0

    # If TVL is available, we can make more specific assertions
    tvl = sdk.vault.get_tvl()
    if tvl > 0:
        # Shares should be proportional to assets
        total_supply = sdk.vault.get_total_supply()
        expected_shares = (assets * total_supply) / tvl
        # Allow for small rounding differences
        assert abs(shares - expected_shares) < Decimal('0.01')


def test_convert_to_assets(sdk):
    """Test converting shares to assets"""
    # Test with 1000 shares
    shares = Decimal('1000.0')
    assets = sdk.vault.convert_to_assets(shares)

    # Assets should be greater than 0
    assert assets > 0

    # If TVL is available, we can make more specific assertions
    tvl = sdk.vault.get_tvl()
    if tvl > 0:
        # Assets should be proportional to shares
        total_supply = sdk.vault.get_total_supply()
        expected_assets = (shares * tvl) / total_supply

        # Calculate relative difference instead of absolute
        relative_diff = abs(assets - expected_assets) / expected_assets
        # Allow for 0.1% difference due to rounding
        assert relative_diff < Decimal(
            '0.001'), f"Relative difference {relative_diff} exceeds tolerance"


def test_convert_roundtrip(sdk):
    """Test that converting assets to shares and back gives approximately the same amount"""
    original_assets = Decimal('1000.0')
    shares = sdk.vault.convert_to_shares(original_assets)
    converted_assets = sdk.vault.convert_to_assets(shares)

    # The roundtrip conversion should be close to the original amount
    # Allow for small rounding differences
    assert abs(original_assets - converted_assets) < Decimal('0.01')


def test_vault_metrics(sdk):
    """Test various vault metrics"""
    # Test TVL
    tvl = sdk.vault.get_tvl()
    assert tvl >= 0

    # Test total supply
    total_supply = sdk.vault.get_total_supply()
    assert total_supply >= 0

    # Test total assets
    total_assets = sdk.vault.get_total_assets()
    assert total_assets >= 0

    # Test available assets
    available_assets = sdk.vault.get_available_assets()
    assert available_assets >= 0
    assert available_assets <= total_assets


def test_share_price_calculation(sdk):
    """Test share price calculation using convert functions"""
    # Get 1 share worth of assets
    one_share = Decimal('1.0')
    assets_for_one_share = sdk.vault.convert_to_assets(one_share)

    # Get 1 asset worth of shares
    one_asset = Decimal('1.0')
    shares_for_one_asset = sdk.vault.convert_to_shares(one_asset)

    # These should be reciprocals of each other (allowing for rounding)
    assert abs(assets_for_one_share * shares_for_one_asset -
               Decimal('1.0')) < Decimal('0.01')

# def test_max_deposit_and_mint(sdk, account):
#     """Test max deposit and mint calculations"""
#     # Test max deposit
#     max_deposit = sdk.vault.max_deposit(account.address)
#     assert max_deposit >= 0

#     # Test max mint
#     max_mint = sdk.vault.max_mint(account.address)
#     assert max_mint >= 0

#     # If we have a max deposit, we should be able to convert it to shares
#     if max_deposit > 0:
#         shares = sdk.vault.convert_to_shares(max_deposit)
#         assert shares > 0


def test_current_epoch_info(sdk):
    """Test current epoch related functions"""
    # Test current epoch
    current_epoch = sdk.vault.get_current_epoch()
    assert current_epoch >= 0

    # Test current epoch start
    epoch_start = sdk.vault.get_current_epoch_start()
    assert epoch_start > 0

    # Test withdraw epochs timelock
    timelock = sdk.vault.get_withdraw_epochs_timelock()
    assert timelock > 0


def test_pnl_related_functions(sdk):
    """Test PnL related functions"""
    # Test accPnlPerToken
    acc_pnl = sdk.vault.get_acc_pnl_per_token()
    assert isinstance(acc_pnl, (int, Decimal))

    # Test currentEpochPositiveOpenPnl
    open_pnl = sdk.vault.get_current_epoch_positive_open_pnl()
    assert open_pnl >= 0


def test_balance_and_allowance(sdk, account):
    """Test balance and allowance functions"""
    # Test balance
    balance = sdk.vault.get_balance(account.address)
    assert balance >= 0

    # Test allowance
    allowance = sdk.vault.allowance(account.address, sdk.vault.vault_address)
    assert allowance >= 0


def test_withdraw_request_functions(sdk, account):
    """Test withdraw request related functions"""
    # Test total shares being withdrawn
    shares_being_withdrawn = sdk.vault.total_shares_being_withdrawn(
        account.address)
    assert shares_being_withdrawn >= 0

    # Test withdraw requests
    current_epoch = sdk.vault.get_current_epoch()
    withdraw_request = sdk.vault.withdraw_requests(
        account.address, current_epoch)
    assert withdraw_request >= 0
