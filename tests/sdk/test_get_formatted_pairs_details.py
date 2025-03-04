import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from ostium_python_sdk.sdk import OstiumSDK
from ostium_python_sdk.config import NetworkConfig

@pytest.fixture
def mock_pair_details():
    return {
        'id': '0',
        'from': 'BTC',
        'to': 'USD',
        'longOI': '410081480598314460',
        'shortOI': '2598123090421427575',
        'maxOI': '1000000000000000000000',
        
        'makerFeeP': '10000',
        'takerFeeP': '100000',
        
        'makerMaxLeverage': '2000',
        'lastFundingRate': '-4813483532',
        'curFundingLong': '-44780202510',
        'curFundingShort': '12384245602',
        'lastFundingBlock': '114601602',
        'group': {
            'name': 'crypto',
            'minLeverage': '100',
            'maxLeverage': '5000',
            'maxCollateralP': '5000'
        },
        'fee': {
            'minLevPos': '250000000'
        }
    }

@pytest.mark.asyncio
async def test_get_formatted_pairs_details(sdk):
    """Test successful retrieval and formatting of pairs details"""
    # Mock subgraph responses
    sdk.subgraph.get_pairs = AsyncMock(return_value=[{'id': '0'}])
    sdk.subgraph.get_pair_details = AsyncMock(return_value=mock_pair_details())
    
    # Mock price response
    sdk.price.get_price = AsyncMock(return_value=(65432.50, True))
    
    # Get formatted pairs
    pairs = await sdk.get_formatted_pairs_details()
    
    # Verify the response
    assert len(pairs) == 1
    pair = pairs[0]
    
    # Check basic pair information
    assert pair['id'] == 0
    assert pair['from'] == 'BTC'
    assert pair['to'] == 'USD'
    assert pair['price'] == 65432.50
    assert pair['isMarketOpen'] is True
    assert pair['group'] == 'crypto'
    
    # Check decimal conversions
    assert pair['longOI'] == Decimal('0.41008148059831446')
    assert pair['shortOI'] == Decimal('2.598123090421427575')
    assert pair['maxOI'] == Decimal('1000')
    assert pair['utilizationP'] == Decimal('80.00')
    assert pair['makerFeeP'] == Decimal('0.01')
    assert pair['takerFeeP'] == Decimal('0.10')    
    assert pair['maxLeverage'] == Decimal('50.00')
    assert pair['minLeverage'] == Decimal('1.00')
    assert pair['makerMaxLeverage'] == Decimal('20.00')
    assert pair['groupMaxCollateralP'] == Decimal('50.00')
    
    # Check funding related fields
    assert pair['lastFundingRate'] == Decimal('-0.004813483532')
    assert pair['curFundingLong'] == Decimal('-0.044780202510')
    assert pair['curFundingShort'] == Decimal('0.012384245602')
    assert pair['lastFundingBlock'] == 114601602

@pytest.mark.asyncio
async def test_get_formatted_pairs_details_price_error(sdk):
    """Test handling of price fetch errors"""
    # Mock subgraph responses
    sdk.subgraph.get_pairs = AsyncMock(return_value=[{'id': '0'}])
    sdk.subgraph.get_pair_details = AsyncMock(return_value=mock_pair_details())
    
    # Mock price response with error
    sdk.price.get_price = AsyncMock(side_effect=ValueError("Price not available"))
    
    # Get formatted pairs
    pairs = await sdk.get_formatted_pairs_details()
    
    # Verify the response handles price error gracefully
    assert len(pairs) == 1
    pair = pairs[0]
    assert pair['price'] == 0
    assert pair['isMarketOpen'] is False 