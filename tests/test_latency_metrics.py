
import unittest

from matching_engine.latency_metrics import LatencyMetrics
from matching_engine.order_book import OrderBook


class TestLatencyMetrics(unittest.TestCase):

    def test_empty_metrics(self):
        metrics = LatencyMetrics()
        self.assertEqual(metrics.summary()["orders_measured"], 0)

    def test_record_latency(self):
        metrics = LatencyMetrics()
        start_ns = metrics.start()
        latency_ns = metrics.stop(start_ns)

        self.assertGreaterEqual(latency_ns, 0)
        self.assertEqual(metrics.summary()["orders_measured"], 1)

    def test_matching_engine_latency(self):
        book = OrderBook()
        metrics = LatencyMetrics()

        start_ns = metrics.start()
        book.add_order(1, 10000, 10, 0)
        latency_ns = metrics.stop(start_ns)

        self.assertGreaterEqual(latency_ns, 0)
        self.assertEqual(metrics.summary()["orders_measured"], 1)


if __name__ == "__main__":
    unittest.main()
