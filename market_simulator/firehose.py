
"""Async mock market-data producer and ring-buffer consumer."""

import argparse
import asyncio
import random
import tempfile
import time
from pathlib import Path

from ipc.ring_buffer import RingBuffer, BufferFull, BufferEmpty


async def run_firehose(
    order_count=100_000,
    capacity=8192,
    report_interval=1.0,
):
    """Generate mock orders and measure end-to-end buffer throughput."""
    if order_count < 1:
        raise ValueError("order_count must be at least 1")

    with tempfile.TemporaryDirectory() as temp_dir:
        buffer_path = Path(temp_dir) / "market_data.bin"

        produced = 0
        consumed = 0
        producer_done = asyncio.Event()
        start_time = time.perf_counter()
        last_report = start_time

        with RingBuffer(buffer_path, capacity=capacity) as ring:
            async def producer():
                nonlocal produced

                while produced < order_count:
                    batch = 0

                    while produced < order_count and batch < 256:
                        order_id = produced + 1
                        price = round(random.uniform(50, 500), 2)
                        quantity = random.randint(1, 1000)
                        side = random.choice(("BUY", "SELL"))

                        try:
                            ring.put(order_id, price, quantity, side)
                            produced += 1
                            batch += 1
                        except BufferFull:
                            break

                    # Yield control so the consumer can drain the buffer.
                    await asyncio.sleep(0)

                producer_done.set()

            async def consumer():
                nonlocal consumed, last_report

                while not producer_done.is_set() or len(ring) > 0:
                    batch = 0

                    while batch < 256:
                        try:
                            ring.get()
                            consumed += 1
                            batch += 1
                        except BufferEmpty:
                            break

                    now = time.perf_counter()

                    if now - last_report >= report_interval:
                        elapsed = now - start_time
                        rate = consumed / elapsed if elapsed else 0
                        print(
                            f"Progress: produced={produced:,}, "
                            f"consumed={consumed:,}, "
                            f"throughput={rate:,.0f} orders/sec"
                        )
                        last_report = now

                    await asyncio.sleep(0)

            await asyncio.gather(producer(), consumer())

        elapsed = time.perf_counter() - start_time
        throughput = consumed / elapsed if elapsed else 0

        results = {
            "target_orders": order_count,
            "produced": produced,
            "consumed": consumed,
            "elapsed_seconds": round(elapsed, 4),
            "orders_per_second": round(throughput, 2),
            "target_100k_reached": throughput >= 100_000,
            "orders_lost": produced - consumed,
        }

        print("\n=== ChronosMatch Firehose Results ===")
        for key, value in results.items():
            print(f"{key}: {value}")

        return results


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark the ChronosMatch async market-data firehose"
    )
    parser.add_argument("--orders", type=int, default=100_000)
    parser.add_argument("--capacity", type=int, default=8192)
    args = parser.parse_args()

    asyncio.run(
        run_firehose(
            order_count=args.orders,
            capacity=args.capacity,
        )
    )


if __name__ == "__main__":
    main()
