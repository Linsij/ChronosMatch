
import tempfile
import unittest
from pathlib import Path

from ipc.ring_buffer import RingBuffer, BufferFull, BufferEmpty


class RingBufferTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "orders.bin"
        self.buffer = RingBuffer(self.path, capacity=2)

    def tearDown(self):
        self.buffer.close()
        self.temp_dir.cleanup()

    def test_write_and_read_order(self):
        self.buffer.put(1, 150.25, 10, "BUY")

        self.assertEqual(
            self.buffer.get(),
            {
                "order_id": 1,
                "price": 150.25,
                "quantity": 10,
                "side": "BUY",
            },
        )

    def test_full_buffer(self):
        self.buffer.put(1, 100.0, 1, "BUY")
        self.buffer.put(2, 101.0, 2, "SELL")

        with self.assertRaises(BufferFull):
            self.buffer.put(3, 102.0, 3, "BUY")

    def test_empty_buffer(self):
        with self.assertRaises(BufferEmpty):
            self.buffer.get()

    def test_wraparound(self):
        self.buffer.put(1, 100.0, 1, "BUY")
        self.buffer.put(2, 101.0, 2, "SELL")
        self.buffer.get()

        self.buffer.put(3, 102.0, 3, "BUY")

        self.assertEqual(self.buffer.get()["order_id"], 2)
        self.assertEqual(self.buffer.get()["order_id"], 3)

    def test_fifo_order(self):
        self.buffer.put(10, 50.0, 1, "BUY")
        self.buffer.put(11, 51.0, 2, "SELL")

        self.assertEqual(self.buffer.get()["order_id"], 10)
        self.assertEqual(self.buffer.get()["order_id"], 11)


if __name__ == "__main__":
    unittest.main()
