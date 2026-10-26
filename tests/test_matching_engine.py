
import unittest

from matching_engine.order_book import OrderBook


class TestMatchingEngine(unittest.TestCase):

    def setUp(self):
        self.book = OrderBook()

    def test_add_buy_order(self):
        self.book.add_order(1, 10000, 10, 0)

        top = self.book.top_of_book()

        self.assertEqual(top["best_bid"], 10000)
        self.assertIsNone(top["best_ask"])

    def test_add_sell_order(self):
        self.book.add_order(1, 10100, 10, 1)

        top = self.book.top_of_book()

        self.assertEqual(top["best_ask"], 10100)

    def test_exact_match(self):
        self.book.add_order(1, 10000, 10, 0)

        trades = self.book.add_order(2, 10000, 10, 1)

        self.assertEqual(trades, [(1, 2, 10000, 10)])
        self.assertIsNone(self.book.top_of_book()["best_bid"])

    def test_partial_fill(self):
        self.book.add_order(1, 10000, 10, 0)

        trades = self.book.add_order(2, 10000, 5, 1)

        self.assertEqual(trades, [(1, 2, 10000, 5)])
        self.assertEqual(self.book.top_of_book()["bid_count"], 1)

    def test_price_priority(self):
        self.book.add_order(1, 10000, 10, 0)
        self.book.add_order(2, 10100, 10, 0)

        trades = self.book.add_order(3, 10000, 5, 1)

        self.assertEqual(trades[0][0], 2)
        self.assertEqual(trades[0][2], 10100)

    def test_time_priority(self):
        self.book.add_order(1, 10000, 10, 0)
        self.book.add_order(2, 10000, 10, 0)

        trades = self.book.add_order(3, 10000, 5, 1)

        self.assertEqual(trades[0][0], 1)

    def test_no_match(self):
        self.book.add_order(1, 9900, 10, 0)
        self.book.add_order(2, 10100, 10, 1)

        top = self.book.top_of_book()

        self.assertEqual(top["best_bid"], 9900)
        self.assertEqual(top["best_ask"], 10100)

    def test_invalid_quantity(self):
        with self.assertRaises(ValueError):
            self.book.add_order(1, 10000, 0, 0)

    def test_invalid_side(self):
        with self.assertRaises(ValueError):
            self.book.add_order(1, 10000, 10, 3)

    def test_multiple_matches(self):
        self.book.add_order(1, 10000, 5, 1)
        self.book.add_order(2, 10100, 5, 1)

        trades = self.book.add_order(3, 10100, 10, 0)

        self.assertEqual(len(trades), 2)
        self.assertEqual(trades[0][1], 1)
        self.assertEqual(trades[1][1], 2)


if __name__ == "__main__":
    unittest.main()
