
"""Run the ChronosMatch firehose benchmark."""

import argparse
import asyncio

from market_simulator.firehose import run_firehose


def main():
    parser = argparse.ArgumentParser()
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
