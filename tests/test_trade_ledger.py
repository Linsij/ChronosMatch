
import os
import tempfile
import unittest

from persistence.trade_ledger import TradeLedger


class TradeLedgerTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = os.path.join(self.temp_dir.name, "test_trades.db")
        self.ledger = TradeLedger(db_path)

    def tearDown(self):
        self.ledger.close()
        self.temp_dir.cleanup()

    def test_insert_and_count_trades(self):
        trades = [
            (101, 201, 1500, 10),
            (102, 202, 1510, 5),
        ]

        inserted = self.ledger.insert_trades(trades)

        self.assertEqual(inserted, 2)
        self.assertEqual(self.ledger.count_trades(), 2)

    def test_retrieve_trades(self):
        trades = [(101, 201, 1500, 10)]

        self.ledger.insert_trades(trades)
        results = self.ledger.get_all_trades()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0:4], trades[0])

    def test_empty_batch(self):
        inserted = self.ledger.insert_trades([])

        self.assertEqual(inserted, 0)
        self.assertEqual(self.ledger.count_trades(), 0)


if __name__ == "__main__":
    unittest.main()
