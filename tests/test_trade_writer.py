
import os
import tempfile
import time
import unittest

from persistence.trade_ledger import TradeLedger
from persistence.trade_writer import TradeWriter


class TradeWriterTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = os.path.join(self.temp_dir.name, "writer_test.db")
        self.ledger = TradeLedger(db_path)

    def tearDown(self):
        self.ledger.close()
        self.temp_dir.cleanup()

    def test_background_trade_persistence(self):
        writer = TradeWriter(
            self.ledger,
            batch_size=2,
            flush_interval=0.2
        )

        writer.start()

        writer.submit((101, 201, 1500, 10))
        writer.submit((102, 202, 1510, 5))
        writer.submit((103, 203, 1520, 8))

        writer.close()

        self.assertEqual(self.ledger.count_trades(), 3)

    def test_single_trade_is_flushed_on_shutdown(self):
        writer = TradeWriter(
            self.ledger,
            batch_size=100,
            flush_interval=10
        )

        writer.start()
        writer.submit((104, 204, 1530, 7))
        writer.close()

        self.assertEqual(self.ledger.count_trades(), 1)

    def test_writer_rejects_submission_after_shutdown(self):
        writer = TradeWriter(self.ledger)
        writer.start()
        writer.close()

        with self.assertRaises(RuntimeError):
            writer.submit((105, 205, 1540, 3))


if __name__ == "__main__":
    unittest.main()
