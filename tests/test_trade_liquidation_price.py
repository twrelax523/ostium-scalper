from ostium_python_sdk.formulae import GetTradeLiquidationPrice
from decimal import Decimal
import unittest


class TestGetTradeLiquidationPrice(unittest.TestCase):

    def setUp(self):
        self.test_cases = [
            # CASE-0
            {
                'openPrice': Decimal('92961.71'),
                'isLong': True,
                'collateral': Decimal('98'),
                'leverage': Decimal('20'),
                'rollover_fee': Decimal('0'),
                'current_funding_fee': Decimal('2757.79'),
                'expected_liq_price': Decimal('219578.879081')
            },
            # CASE-1
            {
                "openPrice":  Decimal("1823.52"),
                "isLong": False,
                "collateral": Decimal("1000"),
                "leverage":   Decimal("100"),
                "rollover_fee": Decimal("10"),
                "current_funding_fee": Decimal("-4"),
                "expected_liq_price": Decimal("1839.8222688"),
            },
            # CASE-2
            {
                "openPrice":  Decimal("129.4"),
                "isLong": True,
                "collateral": Decimal("250"),
                "leverage":   Decimal("20"),
                "rollover_fee": Decimal("5"),
                "current_funding_fee": Decimal("2"),
                "expected_liq_price": Decimal("123.75816"),
            },
            # CASE-3
            {
                "openPrice":  Decimal("27.2"),
                "isLong": False,
                "collateral": Decimal("100"),
                "leverage":   Decimal("2"),
                "rollover_fee": Decimal("2"),
                "current_funding_fee": Decimal("-0.5"),
                "expected_liq_price": Decimal("39.236"),
            },
            # CASE-4
            {
                "openPrice":  Decimal("1.34"),
                "isLong": False,
                "collateral": Decimal("1000"),
                "leverage":   Decimal("50"),
                "rollover_fee": Decimal("23"),
                "current_funding_fee": Decimal("1"),
                "expected_liq_price": Decimal("1.3634768"),
            }
        ]

    def test_trade_liquidation_price(self):
        for case in self.test_cases:
            print(f"\n\n===> case: {case}")
            liq_price = GetTradeLiquidationPrice(
                case['openPrice'],
                case['isLong'],
                case['collateral'],
                case['leverage'],
                case['rollover_fee'],
                case['current_funding_fee']
            )
            self.assertAlmostEqual(
                liq_price,
                case['expected_liq_price'],
                places=5,
                msg=f"Failed for case: {case}"
            )

            # assert pytest.approx(liq_price, rel=Decimal(1e-7)
            #                     ) == case['expected_liq_price']
