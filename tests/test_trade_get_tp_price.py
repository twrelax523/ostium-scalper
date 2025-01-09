import unittest
from constants import MAX_PROFIT_P
from formulae import GetTakeProfitPrice
from decimal import Decimal


class TestGetTradeTpPrice(unittest.TestCase):

    def setUp(self):
        self.test_cases = [
            {
                'openPrice': Decimal('100000'),
                'leverage': Decimal('100'),
                'isLong': True,
                'expected_tp_price': Decimal('109000')
            },
        ]

    def test_get_trade_tp_price(self):
        for case in self.test_cases:
            with self.subTest(case=case):
                sl_price = GetTakeProfitPrice(
                    case['openPrice'],
                    case['leverage'],
                    case['isLong'],
                )
                self.assertAlmostEqual(
                    sl_price,
                    case['expected_tp_price'],
                    places=7,
                    msg=f"Failed for case: {case}"
                )


if __name__ == '__main__':
    unittest.main()
