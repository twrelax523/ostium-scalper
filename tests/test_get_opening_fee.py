import pytest
from decimal import Decimal
from ostium_python_sdk.formulae import getOpeningFee

# Global list of all test cases
test_cases = [
    # CASE-0
    {
        'trade_size': Decimal('-10000'),
        'leverage': Decimal('3'),
        'oi_delta': Decimal('5000'),
        'maker_max_leverage': Decimal('10'),
        'maker_fee_p': Decimal('0.0001'),  # 100 / PRECISION_6 => 0.0001
        'taker_fee_p': Decimal('0.0003'),  # 300 / PRECISION_6 => 0.0003
        'expected_fee': Decimal('0.02')
    }
]


@pytest.mark.parametrize("case", test_cases)
def test_get_opening_fee(case):
    """Test multiple scenarios for getOpeningFee with Pytest."""

    fee = getOpeningFee(
        tradeSize=case['trade_size'],
        leverage=case['leverage'],
        oiDelta=case['oi_delta'],
        makerMaxLeverage=case['maker_max_leverage'],
        makerFeeP=case['maker_fee_p'],
        takerFeeP=case['taker_fee_p']
    )

    # Equivalent to assertAlmostEqual(..., places=5) is approx with abs=1e-5
    # or thereabouts. Adjust as needed for your precision.
    assert fee == pytest.approx(case['expected_fee'], abs=1e-5), \
        f"Failed for case: {case}"
