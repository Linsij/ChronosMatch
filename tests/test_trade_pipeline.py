
import os
import tempfile
import time
import unittest

from ipc.ring_buffer import RingBuffer
from persistence.trade_ledger import TradeLedger
from persistence.trade_pipeline import TradePipeline


class TradePipelineTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        self.buffer = RingBuffer(
            os.path.join(self.temp_dir.name, "orders.mmap"),
            capacity=20
        )

        self.ledger = TradeLedger(
            os.path.join(self.temp_dir.name, "trades.db")
        )

    def tearDown(self):
        self.buffer.close()
        self.ledger.close()
        self.temp_dir.cleanup()

    def test_orders_reach_trade_ledger(self):
        pipeline = TradePipeline(
            self.buffer,
            ledger=self.ledger,
            batch_size=2,
            poll_interval=0.001
        )

        pipeline.start()

        try:
            # First order rests in the book.
            self.buffer.put(1, 100.00, 10, "SELL")

            # Allow the pipeline to process the first order.
            time.sleep(0.05)

            # Second order crosses the resting ask and executes.
            self.buffer.put(2, 100.00, 10, "BUY")

            deadline = time.monotonic() + 2

            while self.ledger.count_trades() == 0:
                if time.monotonic() >= deadline:
                    self.fail("Trade was not persisted within 2 seconds")
                time.sleep(0.01)

        finally:
            pipeline.close()

        self.assertEqual(self.ledger.count_trades(), 1)

        saved = self.ledger.get_all_trades()

        self.assertEqual(saved[0][0], 2)
        self.assertEqual(saved[0][1], 1)
        self.assertEqual(saved[0][2], 10000)
        self.assertEqual(saved[0][3], 10)


if __name__ == "__main__":
    unittest.main()
