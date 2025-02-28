import pytest
from decimal import Decimal, getcontext
from ostium_python_sdk.scscript.funding import getPendingAccFundingFees

@pytest.mark.asyncio
async def test_get_pending_acc_funding_fees_longs_pay_shorts():
    """
    Replicates the scenario from the TypeScript test:
    'Should calculate correct funding rates: longs pay shorts'
    using getPendingAccFundingFees.
    """

    # Set high precision for Decimal calculations
    getcontext().prec = 64

    # -----------------------------------------------------------
    # 1. Define input parameters (matching TypeScript parseUnits())
    #    parseUnits('X', 18) => Decimal('X')
    #    parseUnits('X', 6)  => Decimal('X') * 10^6
    # -----------------------------------------------------------
    acc_per_oi_long = Decimal('0')       # parseUnits('0', 18)
    acc_per_oi_short = Decimal('0')      # parseUnits('0', 18)
    last_funding_rate = Decimal('0')     # parseUnits('0', 18)
    max_funding_fee_per_block = Decimal('0.05')  # parseUnits('0.05', 18) => 0.05
    last_update_block = Decimal('0')
    latest_block = Decimal('1')
    oi_long = Decimal('100') * Decimal('1000000')   # parseUnits('100', 6) => 100 * 10^6
    oi_short = Decimal('100') * Decimal('1000000')  # parseUnits('100', 6) => 100 * 10^6
    oi_cap = Decimal('100000') * Decimal('1000000') # parseUnits('100000', 6)
    hill_inflection_point = Decimal('0.1')          # parseUnits('0.1', 18)
    hill_pos_scale = Decimal('0.94')                # parseUnits('0.94', 2) => 0.94
    hill_neg_scale = Decimal('1.15')                # parseUnits('1.15', 2) => 1.15
    spring_factor = Decimal('0.000005')             # parseUnits('0.000005', 18)
    s_factor_up_scale = Decimal('130')              # parseUnits('130', 2) => 130
    s_factor_down_scale_p = Decimal('90')           # parseUnits('90', 2) => 90

    # -----------------------------------------------------------
    # 2. Define the expected outputs from the TypeScript test
    #    For getPendingAccFundingFees, we typically compare:
    #    (accFundingLong, accFundingShort, latestFundingRate).
    #
    # The TypeScript test also checks targetFr, but that is
    # computed inside GetFundingRate. We'll test only the
    # three returned by getPendingAccFundingFees here.
    # -----------------------------------------------------------
    expected_latest_funding_rate = Decimal('0.000000024999937501')  # parseUnits('0.000000024999937501', 18)
    expected_acc_funding_long = Decimal('0.000000012499979000')     # parseUnits('0.000000012499979000', 18)
    expected_acc_funding_short = Decimal('-0.000000012499979000')   # parseUnits('-0.000000012499979000', 18)
    expected_target_fr = Decimal('0.005') 
    # -----------------------------------------------------------
    # 3. Call getPendingAccFundingFees
    # -----------------------------------------------------------
    acc_funding_long, acc_funding_short, latest_funding_rate_out, target_fr_out = getPendingAccFundingFees(
        blockNumber=latest_block,
        lastUpdateBlock=last_update_block,
        valueLong=acc_per_oi_long,
        valueShort=acc_per_oi_short,
        openInterestUsdcLong=oi_long,
        openInterestUsdcShort=oi_short,
        OiCap=oi_cap,
        maxFundingFeePerBlock=max_funding_fee_per_block,
        lastFundingRate=last_funding_rate,
        hillInflectionPoint=hill_inflection_point,
        hillPosScale=hill_pos_scale,
        hillNegScale=hill_neg_scale,
        springFactor=spring_factor,
        sFactorUpScale=s_factor_up_scale,
        sFactorDownScaleP=s_factor_down_scale_p
    )

    # -----------------------------------------------------------
    # 4. Verify output matches expected (approximately)
    #    If you need exact matching, use str() or more precise checks
    # -----------------------------------------------------------
    assert acc_funding_long == pytest.approx(expected_acc_funding_long, rel=Decimal('1e-12')), \
        f"acc_funding_long is {acc_funding_long}, expected {expected_acc_funding_long}"

    assert acc_funding_short == pytest.approx(expected_acc_funding_short, rel=Decimal('1e-12')), \
        f"acc_funding_short is {acc_funding_short}, expected {expected_acc_funding_short}"

    assert latest_funding_rate_out == pytest.approx(expected_latest_funding_rate, rel=Decimal('1e-12')), \
        f"latest_funding_rate is {latest_funding_rate_out}, expected {expected_latest_funding_rate}" 

    assert target_fr_out == pytest.approx(expected_target_fr, rel=Decimal('1e-12')), \
        f"target_fr is {target_fr_out}, expected {expected_target_fr}"