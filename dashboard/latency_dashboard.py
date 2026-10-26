
"""ChronosMatch live terminal order-book dashboard."""

import curses
import random
import time

from matching_engine.order_book import OrderBook


TICK_SIZE = 0.01


def draw(stdscr, stats):
    stdscr.erase()
    height, width = stdscr.getmaxyx()

    lines = [
        "==========================================",
        "       CHRONOSMATCH LIVE ORDER BOOK",
        "==========================================",
        "",
        f"Best BID       : {stats['bid']}",
        f"Best ASK       : {stats['ask']}",
        f"Spread         : {stats['spread']}",
        "",
        f"Bid orders     : {stats['bid_count']}",
        f"Ask orders     : {stats['ask_count']}",
        f"Executed trades: {stats['trades']}",
        "",
        f"Last latency   : {stats['latency_us']:.2f} us",
        f"Orders/sec     : {stats['rate']:.0f}",
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
    curses.curs_set(0)
    stdscr.nodelay(True)

    book = OrderBook(capacity=100000)

    orders = 0
    trades_count = 0
    start = time.perf_counter()

    while True:
        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            break

        order_id = orders + 1
        price = random.randint(9950, 10050)
        quantity = random.randint(1, 100)
        side = random.randint(0, 1)

        t0 = time.perf_counter_ns()

        try:
            trades = book.add_order(
                order_id, price, quantity, side
            )
        except OverflowError:
            # Stop instead of silently discarding orders.
            break

        latency_us = (time.perf_counter_ns() - t0) / 1000
        trades_count += len(trades)
        orders += 1

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
        rate = orders / elapsed if elapsed > 0 else 0

        draw(stdscr, {
            "bid": bid,
            "ask": ask,
            "spread": spread,
            "bid_count": top["bid_count"],
            "ask_count": top["ask_count"],
            "trades": trades_count,
            "latency_us": latency_us,
            "rate": rate,
        })

        time.sleep(0.05)


if __name__ == "__main__":
    curses.wrapper(main)
