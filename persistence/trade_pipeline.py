
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



"""Connect the mmap order buffer to the matching engine and trade ledger."""

import threading
import time

from ipc.ring_buffer import BufferEmpty
from matching_engine.order_book import OrderBook
from persistence.trade_ledger import TradeLedger
from persistence.trade_writer import TradeWriter


class TradePipeline:
    """Process incoming orders and persist matched trades asynchronously."""

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
        self._started = False
        self._closed = False
        self._lock = threading.Lock()

    def start(self):
        """Start the asynchronous trade writer and pipeline worker."""

        with self._lock:
            if self._started:
                raise RuntimeError("Pipeline has already been started")

            if self._closed:
                raise RuntimeError("Pipeline is already closed")

            self._started = True

        try:
            self.writer.start()

            self.worker = threading.Thread(
                target=self._run,
                name="TradePipeline",
                daemon=True,
            )
            self.worker.start()

        except Exception:
            self.stop_event.set()
            self.writer.close()
            raise

    def _process_order(self, order):
        """Send an order to the matching engine."""

        side = order["side"].upper()

        if side not in ("BUY", "SELL"):
            raise ValueError(f"Invalid order side: {side}")

        side_code = 0 if side == "BUY" else 1

        price = int(round(float(order["price"]) * 100))

        if price <= 0:
            raise ValueError("Order price must be positive")

        if int(order["quantity"]) <= 0:
            raise ValueError("Order quantity must be positive")

        trades = self.order_book.add_order(
            order["order_id"],
            price,
            int(order["quantity"]),
            side_code,
        )

        for trade in trades:
            self.writer.submit(trade)

    def _run(self):
        """Continuously consume orders and process matched trades."""

        try:
            while True:

                try:
                    order = self.buffer.get()

                except BufferEmpty:
                    if self.stop_event.is_set():
                        break

                    time.sleep(self.poll_interval)
                    continue

                self._process_order(order)

        except Exception as exc:
            self.error = exc
            self.stop_event.set()

    def close(self):
        """Stop processing, drain available orders and flush pending trades."""

        with self._lock:
            if self._closed:
                return

            self._closed = True

        self.stop_event.set()

        if self.worker is not None:
            self.worker.join()

        try:
            self.writer.close()

        except Exception:
            if self.error is not None:
                raise RuntimeError(
                    "Trade pipeline failed"
                ) from self.error
            raise

        if self.error is not None:
            raise RuntimeError(
                "Trade pipeline failed"
            ) from self.error

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False
