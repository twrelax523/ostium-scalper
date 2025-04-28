import pytest
from web3 import Web3
from ostium_python_sdk import OstiumSDK
from unittest.mock import Mock

# Test constants
TEST_RPC_URL = "https://arb-sepolia.g.alchemy.com/v2/xussaWLkWxKtZjCIlUjAYiMGV6_dRO-8"
TEST_PRIVATE_KEY = "0x" + "1" * 64  # Example private key
VALID_PAIR_ID = 0
VALID_TRADE_INDEX = 0

@pytest.fixture
def sdk_without_key():
    return OstiumSDK("testnet", rpc_url=TEST_RPC_URL)

@pytest.fixture
def sdk_with_key():
    return OstiumSDK("testnet", private_key=TEST_PRIVATE_KEY, rpc_url=TEST_RPC_URL)

class TestSDKPrivateKey:
    def test_write_operation_fails_without_key(self, sdk_without_key):
        """
        Test that write operations fail when SDK is instantiated without a private key
        and no key is provided to the method
        """
        with pytest.raises(ValueError, match="No private key provided"):
            sdk_without_key.ostium.close_trade(
                pair_id=VALID_PAIR_ID,
                trade_index=VALID_TRADE_INDEX
            )

    def test_write_operation_succeeds_with_method_key(self, sdk_without_key):
        """
        Test that write operations succeed when private key is provided to the method,
        even if SDK was instantiated without one
        """
        # Mock the web3 transaction to avoid actual blockchain calls
        sdk_without_key.ostium.web3.eth.get_transaction_count = Mock(return_value=1)
        sdk_without_key.ostium.web3.eth.send_raw_transaction = Mock(return_value=b'0x123')
        sdk_without_key.ostium.web3.eth.wait_for_transaction_receipt = Mock(return_value={'status': 1})

        # Should not raise any exception
        result = sdk_without_key.ostium.close_trade(
            pair_id=VALID_PAIR_ID,
            trade_index=VALID_TRADE_INDEX,
            private_key=TEST_PRIVATE_KEY
        )
        assert result is not None

    def test_write_operation_succeeds_with_sdk_key(self, sdk_with_key):
        """
        Test that write operations succeed when SDK is instantiated with a private key
        """
        # Mock the web3 transaction to avoid actual blockchain calls
        sdk_with_key.ostium.web3.eth.get_transaction_count = Mock(return_value=1)
        sdk_with_key.ostium.web3.eth.send_raw_transaction = Mock(return_value=b'0x123')
        sdk_with_key.ostium.web3.eth.wait_for_transaction_receipt = Mock(return_value={'status': 1})

        # Should not raise any exception
        result = sdk_with_key.get_open_trades()
        assert result is not None

    @pytest.mark.parametrize("write_operation", [
        "close_trade",
        "perform_trade",
        "remove_collateral",
        "add_collateral",
        "update_tp",
        "update_sl",
        # "update_limit_order",
        # "cancel_limit_order",
        # "withdraw",
        # "update_limit_order",
        # "cancel_limit_order",
        
        # Add other write operations here
    ])
    def test_all_write_operations_require_key(self, sdk_without_key, write_operation):
        """
        Test that all write operations fail without a private key
        """
        method = getattr(sdk_without_key.ostium, write_operation)
        
        with pytest.raises(ValueError, match="No private key provided"):
            if write_operation == "perform_trade":
                method(trade_params={}, at_price=1000)
            elif write_operation == "add_collateral":
                method(pair_id=1, trade_index=0, collateral_amount=100)
            elif write_operation == "remove_collateral":
                method(pair_id=1, trade_index=0, remove_amount=100)
            elif write_operation == "update_tp":
                method(pair_id=1, trade_index=0, tp_price=10000)
            elif write_operation == "update_sl":
                method(pair_id=1, trade_index=0, sl_price=10000)
            else:
                method(pair_id=1, trade_index=0)

    def test_write_operation_requires_single_key_source(self, sdk_with_key):
        """
        Test that we can use either SDK's default key (from env) OR method-level key, but not both.
        Using both should raise a ValueError.
        """
        method_level_key = "0x" + "2" * 64
        
        # Should work with default key
        sdk_address = sdk_with_key.ostium.get_public_address()
        assert sdk_address is not None
        
        # Should work with method key on SDK without default key
        sdk_without_default = OstiumSDK("testnet", rpc_url=TEST_RPC_URL)  # No default key
        method_address = sdk_without_default.ostium.get_public_address(private_key=method_level_key)
        assert method_address is not None
        
        # Should fail when trying to use both
        with pytest.raises(ValueError, match="Cannot provide both private key and default private key"):
            sdk_with_key.ostium.get_public_address(private_key=method_level_key) 