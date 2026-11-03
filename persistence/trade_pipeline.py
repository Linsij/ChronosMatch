
"""Connect the mmap order buffer to the matching engine and trade ledger."""

import threading

from ipc.ring_buffer import BufferEmpty
from matching_engine.order_book import OrderBook
from persistence.trade_ledger import TradeLedger
from persistence.trade_writer import TradeWriter


class TradePipeline:
    def __init__(
        self,
        buffer,
        ledger=None,
        order_book=None,
        batch_size=50,
        poll_interval=0.01,
    ):
        self.buffer = buffer
        self.ledger = ledger or TradeLedger()
        self.order_book = order_book or OrderBook()

        self.writer = TradeWriter(
            self.ledger,
            batch_size=batch_size,
            flush_interval=0.5,
        )

        self.poll_interval = poll_interval
        self.stop_event = threading.Event()
        self.worker = None
        self.error = None

    def start(self):
        if self.worker is not None:
            raise RuntimeError("Pipeline has already been started")

        self.writer.start()

        self.worker = threading.Thread(
            target=self._run,
            name="TradePipeline",
            daemon=True,
        )
        self.worker.start()

    def _run(self):
        import time

        try:
            while not self.stop_event.is_set():
                try:
                    order = self.buffer.get()
                except BufferEmpty:
                    time.sleep(self.poll_interval)
                    continue

                side = 0 if order["side"] == "BUY" else 1

                trades = self.order_book.add_order(
                    order["order_id"],
                    int(round(order["price"] * 100)),
                    order["quantity"],
                    side,
                )

                for trade in trades:
                    self.writer.submit(trade)

        except Exception as exc:
            self.error = exc
            self.stop_event.set()

    def close(self):
        self.stop_event.set()

        if self.worker is not None:
            self.worker.join()

        try:
            self.writer.close()
        finally:
            if self.error is not None:
                raise RuntimeError(
                    "Trade pipeline failed"
                ) from self.error
