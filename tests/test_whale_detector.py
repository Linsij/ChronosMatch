
import unittest

from dashboard.whale_detector import WhaleDetector


class WhaleDetectorTests(unittest.TestCase):

    def setUp(self):
        self.detector = WhaleDetector(
            quantity_threshold=1000,
            level_threshold=2
        )

    def test_detect_large_buy_order(self):
        trades = [
            (101, 201, 1500, 600),
            (101, 202, 1510, 500),
        ]

        result = self.detector.detect(trades, 0)

        self.assertIsNotNone(result)
        self.assertEqual(result["side"], "BUY")
        self.assertEqual(result["total_quantity"], 1100)
        self.assertEqual(result["levels_cleared"], 2)

    def test_ignore_small_trade(self):
        trades = [
            (101, 201, 1500, 400),
            (101, 202, 1510, 300),
        ]

        result = self.detector.detect(trades, 0)

        self.assertIsNone(result)

    def test_ignore_single_price_level(self):
        trades = [
            (101, 201, 1500, 600),
            (101, 202, 1500, 500),
        ]

        result = self.detector.detect(trades, 0)

        self.assertIsNone(result)

    def test_detect_large_sell_order(self):
        trades = [
            (201, 301, 1490, 700),
            (202, 301, 1480, 400),
        ]

        result = self.detector.detect(trades, 1)

        self.assertIsNotNone(result)
        self.assertEqual(result["side"], "SELL")
        self.assertEqual(result["levels_cleared"], 2)

    def test_invalid_side(self):
        with self.assertRaises(ValueError):
            self.detector.detect([], 2)


if __name__ == "__main__":
    unittest.main()
