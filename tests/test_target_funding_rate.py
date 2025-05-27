import os
import pytest
from dotenv import load_dotenv
from ostium_python_sdk import OstiumSDK
from ostium_python_sdk.config import NetworkConfig


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


@pytest.mark.asyncio
async def test_target_funding_rate_for_btc_usd(sdk):
    target_funding_rate = await sdk.get_target_funding_rate(0)
    print(f"target_funding_rate: {target_funding_rate}")

    assert target_funding_rate == pytest.approx(1, abs=1), \
        f"Failed target_funding_rate assertion for BTC/USD"
