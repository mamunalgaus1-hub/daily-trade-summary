import unittest

import daily_summary as ds

CSV = """close_time,symbol,profit
2026-10-05 09:00:00,XAUUSD,10
2026-10-05 10:00:00,XAUUSD,-4
2026-10-06 09:00:00,XAUUSD,-6
bad row,XAUUSD,oops
"""


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.trades = ds.parse_trades(CSV)

    def test_bad_rows_are_skipped(self):
        self.assertEqual(len(self.trades), 3)

    def test_daily_numbers(self):
        day1, day2 = ds.summarise(self.trades)
        self.assertEqual(day1.trades, 2)
        self.assertAlmostEqual(day1.net, 6)
        self.assertAlmostEqual(day1.profit_factor, 2.5)
        self.assertEqual(day2.wins, 0)
        self.assertIsNone(ds.summarise(self.trades[:1])[0].profit_factor)

    def test_max_drawdown(self):
        # equity: 10 -> 6 -> 0, peak 10, so drawdown 10
        self.assertAlmostEqual(ds.max_drawdown(self.trades), 10)

    def test_missing_column(self):
        with self.assertRaises(ValueError):
            ds.parse_trades("close_time,symbol\n2026-10-05,XAUUSD\n")


if __name__ == "__main__":
    unittest.main()
