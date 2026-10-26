
"""Benchmark the ChronosMatch Cython matching engine."""

import argparse
import random
import statistics
import time

from matching_engine.order_book import OrderBook


def benchmark(order_count=100_000):
    random.seed(42)

    book = OrderBook(capacity=order_count + 100)
    latencies_ns = []
    trades_count = 0

    start = time.perf_counter()

    for order_id in range(1, order_count + 1):
        price = random.randint(9950, 10050)
        quantity = random.randint(1, 100)
        side = random.randint(0, 1)

        t0 = time.perf_counter_ns()
        trades = book.add_order(order_id, price, quantity, side)
        latency = time.perf_counter_ns() - t0

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--orders", type=int, default=100_000)
    args = parser.parse_args()

    if args.orders < 1:
        parser.error("--orders must be at least 1")

    benchmark(args.orders)
