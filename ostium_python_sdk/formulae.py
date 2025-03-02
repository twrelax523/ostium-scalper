from decimal import Decimal, getcontext, ROUND_DOWN
from .constants import MAX_PROFIT_P, MAX_STOP_LOSS_P, PRECISION_16, PRECISION_2, PRECISION_6, PRECISION_12, PRECISION_18, LIQ_THRESHOLD_P
from typing import Dict
from .scscript.funding import getPendingAccFundingFees, getTargetFundingRate

quantization_6 = Decimal('0.000001')
quantization_18 = Decimal('0.000000000000000001')

# v2 (formulae v1.3.3)
def GetTakeProfitPrice(open_price: Decimal, profit_p: Decimal, leverage: Decimal, is_long: bool) -> Decimal:
    open_price = Decimal(open_price)
    profit_p = Decimal(profit_p)
    leverage = Decimal(leverage)

    price_diff = (open_price * profit_p) / (leverage * Decimal('100'))

    if (is_long):
        tp_price = open_price + price_diff 
    else:
        tp_price = open_price - price_diff 

    return Decimal(tp_price if tp_price > 0 else '0')

# v2 (formulae v1.3.3)
def GetStopLossPrice(open_price: Decimal, loss_p: Decimal, leverage: Decimal, is_long: bool) -> Decimal:
    open_price = Decimal(open_price)
    loss_p = Decimal(loss_p)
    leverage = Decimal(leverage)

    # price_diff matches your existing TP logic style, except using 'loss_p'
    price_diff = (open_price * loss_p) / (leverage * Decimal('100'))

    sl_price = open_price - price_diff if is_long else open_price + price_diff
    return sl_price if sl_price > 0 else Decimal('0')

# v2 (formulae v1.3.3)
def CurrentTradeProfitP(
    open_price: Decimal,
    current_price: Decimal,
    long: bool,
    leverage: Decimal,
    highest_leverage: Decimal
) -> Decimal:
    leverage_to_use = leverage if leverage > highest_leverage else highest_leverage
    if long:
        price_diff = current_price - open_price
    else:
        price_diff = open_price - current_price

    profit_p = (price_diff / open_price) * leverage_to_use * Decimal("100")

    if profit_p >= MAX_PROFIT_P:
        profit_p = MAX_PROFIT_P
    
    profit_p *= (leverage / leverage_to_use)

    return profit_p

# v2 (formulae v1.3.3)
def TopUpWithCollateral(
    leverage: Decimal,
    collateral: Decimal,
    added_collateral: Decimal
) -> Decimal:
    new_leverage = (collateral * leverage) / (collateral + added_collateral)
    return new_leverage
# tbd - used by SDK


def GetTradeLiquidationPrice(
    open_price: str,
    long: bool,
    collateral: str,
    leverage: str,
    rollover_fee: str,
    funding_fee: str
) -> Decimal:
    try:
        open_price = Decimal(open_price)
        collateral = Decimal(collateral)
        rollover_fee = Decimal(rollover_fee)
        funding_fee = Decimal(funding_fee)
        leverage = Decimal(leverage)

        liq_price_distance = (
            open_price *
            (collateral * Decimal(LIQ_THRESHOLD_P) / Decimal(100) - rollover_fee - funding_fee) /
            collateral /
            leverage
        )

        liq_price = open_price - liq_price_distance if long else open_price + liq_price_distance
        liq_price = liq_price if liq_price > 0 else 0
        return liq_price

    except Exception as error:
        raise Exception(f"Unable to compute Liquidation Price: {error}")


def GetCurrentRolloverFee(
    acc_rollover: str,
    last_rollover_block: str,
    rollover_fee_per_block: str,
    latest_block: str
) -> Decimal:
    try:
        acc_rollover = Decimal(acc_rollover)
        last_rollover_block = Decimal(last_rollover_block)
        rollover_fee_per_block = Decimal(rollover_fee_per_block)
        latest_block = Decimal(latest_block)
        current_fee = acc_rollover + \
            (latest_block - last_rollover_block) * rollover_fee_per_block
        return current_fee

    except Exception as error:
        raise Exception(f"Unable to compute Current Rollover Fee: {error}")


def GetTradeRolloverFee(
    trade_rollover: str,
    current_rollover: str,
    collateral: str,
    leverage: str
) -> Decimal:
    try:
        current_rollover = Decimal(current_rollover)
        trade_rollover = Decimal(trade_rollover)
        collateral = Decimal(collateral)
        leverage = Decimal(leverage)

        rollover_fee = (
            (current_rollover - trade_rollover) *
            collateral *
            leverage /
            PRECISION_18 /
            PRECISION_2
        )
        return rollover_fee

    except Exception as error:
        raise Exception(f"Unable to compute Trade Rollover Fee: {error}")

# Gets the funding fee (abs) for an open trade (up to this block, aka based on current_funding up till this block)


def GetTradeFundingFee(
    trade_funding: str,
    current_funding: str,
    collateral: str,
    leverage: str
) -> Decimal:
    try:
        current_funding = Decimal(current_funding)
        trade_funding = Decimal(trade_funding)
        collateral = Decimal(collateral)
        leverage = Decimal(leverage)

        funding_fee = (
            (current_funding - trade_funding) *
            collateral *
            leverage /
            PRECISION_18 /
            PRECISION_2
        )
        return funding_fee

    except Exception as error:
        raise Exception(f"Unable to compute Trade Funding Fee: {error}")


def GetPriceImpact(
    mid_price: str,
    bid_price: str,
    ask_price: str,
    is_open: bool,
    is_long: bool,  # aka is_long
) -> dict:
    try:
        mid_price = Decimal(mid_price)
        bid_price = Decimal(bid_price)
        ask_price = Decimal(ask_price)

        if (mid_price == 0):
            return {
                'priceImpactP': str(0),
                'priceAfterImpact': str(0)
            }

        above_spot = is_open == is_long
        used_price = ask_price if above_spot else bid_price
        priceImpactP = 100 * (abs(mid_price - used_price) / mid_price)

        return {
            'priceImpactP': str(priceImpactP),
            'priceAfterImpact': str(used_price)
        }

    except Exception as error:
        raise Exception(f"Unable to compute Price Impact: {error}")


# calculates the gross (without fees) profit (abs) of an open trade
def CurrentTradeProfitRaw(
    open_price: str,
    current_price: str,
    is_buy: bool,
    leverage: str,
    collateral: str
) -> str:
    try:
        open_price = Decimal(open_price)
        current_price = Decimal(current_price)
        leverage = Decimal(leverage)
        collateral = Decimal(collateral)

        # Calculate price difference based on position direction
        if is_buy:
            price_diff = current_price - open_price
        else:
            price_diff = open_price - current_price

        # Calculate profit
        profit = (price_diff * collateral * leverage) / \
            (open_price * PRECISION_2)

        return str(profit)

    except Exception as error:
        raise Exception(f"Unable to compute Current Trade Profit Raw: {error}")

# calculates the net profit (after fees) of an open trade (abs)


def CurrentTotalProfitRaw(
    open_price: str,
    current_price: str,
    is_buy: bool,
    leverage: str,
    collateral: str,
    rollover_fee: str,
    funding_fee: str
) -> str:
    try:
        # Get trade profit
        trade_profit = Decimal(CurrentTradeProfitRaw(
            open_price,
            current_price,
            is_buy,
            leverage,
            collateral
        ))

        # Subtract fees
        total_profit = trade_profit - \
            Decimal(rollover_fee) - Decimal(funding_fee)

        return str(total_profit)

    except Exception as error:
        raise Exception(f"Unable to compute Current Total Profit Raw: {error}")


# TBD- used by sdk. calculates the net profit percentage of an open trade
# What's the diff between this and CurrentTradeProfitP?
def CurrentTotalProfitP(total_profit: str, collateral: str) -> str:
    try:
        total_profit = Decimal(total_profit)
        collateral = Decimal(collateral)

        # Calculate profit percentage
        profit_percentage = (total_profit * PRECISION_6) / collateral

        # Cap at MAX_PROFIT_P if needed
        if profit_percentage > MAX_PROFIT_P:
            return str(MAX_PROFIT_P)

        return str(profit_percentage)

    except Exception as error:
        raise Exception(
            f"Unable to compute Current Total Profit Percentage: {error}")


# returns (acc_funding_long, acc_funding_short, latest_funding_rate, target_fr)
# latest_funding_rate and target_fr are per block
def GetFundingRateV2(
    acc_per_oi_long: str,
    acc_per_oi_short: str,
    last_funding_rate: str,
    max_funding_fee_per_block: str,
    last_update_block: str,
    latest_block: str,
    oi_long: str,
    oi_short: str,
    oi_cap: str,
    hill_inflection_point: str,
    hill_pos_scale: str,
    hill_neg_scale: str,
    spring_factor: str,
    s_factor_up_scale_p: str,
    s_factor_down_scale_p: str,
    verbose: bool = False
) -> dict:
    """
    Calculate funding rates and return as integers multiplied by PRECISION_18
    Returns: (acc_funding_long, acc_funding_short, latest_funding_rate, target_fr)
    """
    def log(message):
        if verbose:
            print(message)

    # Set decimal precision
    getcontext().prec = 128
    getcontext().rounding = ROUND_DOWN

    # Convert all inputs to Decimal
    oi_long_dec = Decimal(oi_long)
    oi_short_dec = Decimal(oi_short)
    oi_cap_dec = Decimal(oi_cap)

    log(f"Input values:")
    log(f"OI Long: {oi_long_dec}")
    log(f"OI Short: {oi_short_dec}")
    log(f"OI Cap: {oi_cap_dec}")
    log(f"Last Funding Rate: {last_funding_rate}")
    log(f"Last Update Block: {last_update_block}")
    log(f"Latest Block: {latest_block}")

    # Calculate normalized OI delta
    open_interest_max = max(oi_long_dec, oi_short_dec)
    normalized_oi_delta = ((oi_long_dec - oi_short_dec)
                           * PRECISION_6) / max(oi_cap_dec, open_interest_max)

    log(f"\nCalculated values:")
    log(f"Open Interest Max: {open_interest_max}")
    log(f"Normalized OI Delta: {normalized_oi_delta}")

    # Get funding values
    acc_funding_long, acc_funding_short, latest_funding_rate, target_fr = getPendingAccFundingFees(
        blockNumber=Decimal(latest_block),
        lastUpdateBlock=Decimal(last_update_block),
        valueLong=Decimal(acc_per_oi_long),
        valueShort=Decimal(acc_per_oi_short),
        openInterestUsdcLong=oi_long_dec,
        openInterestUsdcShort=oi_short_dec,
        OiCap=oi_cap_dec,
        maxFundingFeePerBlock=Decimal(max_funding_fee_per_block),
        lastFundingRate=Decimal(last_funding_rate),
        hillInflectionPoint=Decimal(hill_inflection_point),
        hillPosScale=Decimal(hill_pos_scale),
        hillNegScale=Decimal(hill_neg_scale),
        springFactor=Decimal(spring_factor),
        sFactorUpScale=Decimal(s_factor_up_scale_p),
        sFactorDownScaleP=Decimal(s_factor_down_scale_p),
    )

    # log(f"\nIntermediate results:")
    # log(f"Acc Funding Long (pre-conversion): {acc_funding_long}")
    # log(f"Acc Funding Short (pre-conversion): {acc_funding_short}")
    # log(f"Latest Funding Rate (pre-conversion): {latest_funding_rate}")
    # log(f"Target Funding Rate (pre-conversion): {target_fr}")

    acc_funding_long = (
        acc_funding_long / PRECISION_18).quantize(quantization_18, rounding=ROUND_DOWN)
    acc_funding_short = (
        acc_funding_short / PRECISION_18).quantize(quantization_18, rounding=ROUND_DOWN)
    latest_funding_rate = (
        latest_funding_rate / PRECISION_18).quantize(quantization_18, rounding=ROUND_DOWN)
    target_fr = (target_fr / PRECISION_18).quantize(quantization_18,
                                                    rounding=ROUND_DOWN)

    # log(f"\nFinal results (multiplied by 10^18):")
    # log(f"Acc Funding Long: {acc_funding_long}")
    # log(f"Acc Funding Short: {acc_funding_short}")
    # log(f"Latest Funding Rate: {latest_funding_rate}")
    # log(f"Target Funding Rate: {target_fr}")

    return {
        'accFundingLong': acc_funding_long,
        'accFundingShort': acc_funding_short,
        'latestFundingRate': ((latest_funding_rate).quantize(quantization_6, rounding=ROUND_DOWN)),
        'targetFundingRate': ((target_fr).quantize(quantization_6, rounding=ROUND_DOWN))
    }
