
"""ChronosMatch live terminal order-book dashboard."""

import curses
import random
import time

from matching_engine.order_book import OrderBook
from dashboard.whale_detector import WhaleDetector
from persistence.trade_ledger import TradeLedger
from persistence.trade_writer import TradeWriter


TICK_SIZE = 0.01
WHALE_QUANTITY = 100
WHALE_LEVELS = 2
REFRESH_INTERVAL = 0.05


def draw(stdscr, stats):
    """Render live order-book and performance information."""

    stdscr.erase()
    height, width = stdscr.getmaxyx()

    lines = [
        "=" * 45,
        "          CHRONOSMATCH LIVE DASHBOARD",
        "=" * 45,
        "",
        "----------- ORDER BOOK ----------------",
        f"Best BID          : {stats['bid']}",
        f"Best ASK          : {stats['ask']}",
        f"Spread            : {stats['spread']}",
        f"Bid orders        : {stats['bid_count']}",
        f"Ask orders        : {stats['ask_count']}",
        "",
        "----------- EXECUTION METRICS ---------",
        f"Orders processed  : {stats['orders']}",
        f"Executed trades   : {stats['trades']}",
        f"Average latency   : {stats['avg_latency']:.2f} us",
        f"Maximum latency   : {stats['max_latency']:.2f} us",
        f"Last latency      : {stats['latency_us']:.2f} us",
        f"Throughput        : {stats['rate']:.0f} orders/sec",
        "",
        "----------- WHALE ORDER ALERT ---------",
        f"Total alerts      : {stats['whale_count']}",
        stats["whale_alert"],
        "",
        "Press Q to quit",
    ]

    for row, line in enumerate(lines):
        if row >= height:
            break

        try:
            stdscr.addnstr(row, 0, line, max(0, width - 1))
        except curses.error:
            pass

    stdscr.refresh()


def main(stdscr):
    """Run the ChronosMatch live trading dashboard."""

    curses.curs_set(0)
    stdscr.nodelay(True)

    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_RED, -1)

    book = OrderBook(capacity=100000)

    detector = WhaleDetector(
        quantity_threshold=WHALE_QUANTITY,
        level_threshold=WHALE_LEVELS,
    )

    ledger = TradeLedger()

    writer = TradeWriter(
        ledger,
        batch_size=50,
        flush_interval=0.5,
    )

    orders = 0
    trades_count = 0
    whale_count = 0

    total_latency = 0
    max_latency = 0
    start = time.perf_counter()

    whale_alert = "No whale orders detected yet"

    try:
        writer.start()

        while True:

            key = stdscr.getch()

            if key in (ord("q"), ord("Q")):
                break

            # Generate simulated market orders.
            order_id = orders + 1
            price = random.randint(9950, 10050)

            # Occasionally generate larger orders for whale detection.
            if orders > 0 and orders % 50 == 0:
                quantity = random.randint(150, 250)
            else:
                quantity = random.randint(1, 100)

            side = random.randint(0, 1)

            # Measure matching-engine execution latency.
            t0 = time.perf_counter_ns()

            try:
                trades = book.add_order(
                    order_id,
                    price,
                    quantity,
                    side,
                )

            except OverflowError:
                whale_alert = "Order book capacity reached"
                break

            latency_us = (
                time.perf_counter_ns() - t0
            ) / 1000

            orders += 1
            trades_count += len(trades)

            total_latency += latency_us
            max_latency = max(max_latency, latency_us)

            # Persist matched trades asynchronously.
            for trade in trades:
                writer.submit(trade)

            # Detect large orders sweeping multiple price levels.
            whale = detector.detect(trades, side)

            if whale:
                whale_count += 1

                whale_alert = (
                    f"{whale['side']} | "
                    f"Quantity: {whale['total_quantity']} | "
                    f"Levels: {whale['levels_cleared']} | "
                    f"Prices: {whale['execution_prices']}"
                )

            # Read current order-book state.
            top = book.top_of_book()

            bid_ticks = top["best_bid"]
            ask_ticks = top["best_ask"]

            bid = (
                f"{bid_ticks * TICK_SIZE:.2f}"
                if bid_ticks is not None else "N/A"
            )

            ask = (
                f"{ask_ticks * TICK_SIZE:.2f}"
                if ask_ticks is not None else "N/A"
            )

            spread = (
                f"{(ask_ticks - bid_ticks) * TICK_SIZE:.2f}"
                if bid_ticks is not None and ask_ticks is not None
                else "N/A"
            )

            elapsed = time.perf_counter() - start

            rate = (
                orders / elapsed
                if elapsed > 0 else 0
            )

            avg_latency = (
                total_latency / orders
                if orders > 0 else 0
            )

            stats = {
                "bid": bid,
                "ask": ask,
                "spread": spread,
                "bid_count": top["bid_count"],
                "ask_count": top["ask_count"],
                "orders": orders,
                "trades": trades_count,
                "latency_us": latency_us,
                "avg_latency": avg_latency,
                "max_latency": max_latency,
                "rate": rate,
                "whale_count": whale_count,
                "whale_alert": whale_alert,
            }

            draw(stdscr, stats)

            time.sleep(REFRESH_INTERVAL)

    finally:
        # Flush pending trades before closing SQLite.
        try:
            writer.close()
        finally:
            ledger.close()


if __name__ == "__main__":
    curses.wrapper(main)
