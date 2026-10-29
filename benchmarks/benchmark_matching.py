
"""Benchmark the ChronosMatch Cython matching engine."""

import argparse
import random
import statistics
import time
from matching_engine.latency_metrics import LatencyMetrics

from matching_engine.order_book import OrderBook


def benchmark(order_count=100_000):
    random.seed(42)

    book = OrderBook(capacity=order_count + 100)
    metrics = LatencyMetrics()
    latencies_ns = []
    trades_count = 0

    start = time.perf_counter()

    for order_id in range(1, order_count + 1):
        price = random.randint(9950, 10050)
        quantity = random.randint(1, 100)
        side = random.randint(0, 1)

        start_ns = metrics.start()
        trades = book.add_order(order_id, price, quantity, side)
        latency = metrics.stop(start_ns)
        latencies_ns.append(latency)
        trades_count += len(trades)

    elapsed = time.perf_counter() - start

    sorted_latencies = sorted(latencies_ns)

    def percentile(p):
        index = min(
            len(sorted_latencies) - 1,
            max(0, int((len(sorted_latencies) - 1) * p))
        )
        return sorted_latencies[index] / 1000

    print("\n=== ChronosMatch Matching Engine Benchmark ===")
    print(f"Orders processed: {order_count:,}")
    print(f"Trades executed: {trades_count:,}")
    print(f"Elapsed time: {elapsed:.4f} seconds")
    print(f"Throughput: {order_count / elapsed:,.2f} orders/sec")
    print(f"Average latency: {statistics.mean(latencies_ns) / 1000:.2f} us")
    print(f"P50 latency: {percentile(0.50):.2f} us")
    print(f"P95 latency: {percentile(0.95):.2f} us")
    print(f"P99 latency: {percentile(0.99):.2f} us")
    summary = metrics.summary()

    print("\n=== Nanosecond Latency Metrics ===")
    print(f"Orders measured: {summary['orders_measured']:,}")
    print(f"Average latency: {summary['average_ns']:.2f} ns")
    print(f"Minimum latency: {summary['min_ns']:,} ns")
    print(f"Maximum latency: {summary['max_ns']:,} ns")
    print(f"P50 latency: {summary['p50_ns']:,} ns")
    print(f"P95 latency: {summary['p95_ns']:,} ns")
    print(f"P99 latency: {summary['p99_ns']:,} ns")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--orders", type=int, default=100_000)
    args = parser.parse_args()

    if args.orders < 1:
        parser.error("--orders must be at least 1")

    benchmark(args.orders)
