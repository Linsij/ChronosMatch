
"""Asynchronous batch persistence for ChronosMatch trades."""

import queue
import threading
import time


class TradeWriter:
    """Persist matched trades using a background worker."""

    def __init__(
        self,
        ledger,
        batch_size=100,
        flush_interval=1.0,
        max_retries=3,
    ):
        if batch_size <= 0:
            raise ValueError("Batch size must be positive")

        if flush_interval <= 0:
            raise ValueError("Flush interval must be positive")

        if max_retries <= 0:
            raise ValueError("Max retries must be positive")

        self.ledger = ledger
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_retries = max_retries

        self.trade_queue = queue.Queue()
        self.stop_event = threading.Event()

        self.worker = None
        self.error = None
        self.started = False
        self.closed = False

        self._lock = threading.Lock()
        self.persisted_count = 0
        self.failed_count = 0

    def start(self):
        """Start the background persistence worker."""

        with self._lock:
            if self.started:
                return

            if self.closed:
                raise RuntimeError(
                    "A closed trade writer cannot be restarted"
                )

            self.started = True

            self.worker = threading.Thread(
                target=self._run,
                name="TradeWriter",
                daemon=True,
            )

            try:
                self.worker.start()
            except Exception:
                self.started = False
                self.worker = None
                raise

    def submit(self, trade):
        """Submit a matched trade for asynchronous persistence."""

        with self._lock:
            if (
                not self.started
                or self.closed
                or self.stop_event.is_set()
                or self.error is not None
            ):
                raise RuntimeError(
                    "Trade writer is not accepting trades"
                )

            self.trade_queue.put(trade)

    def _save_batch(self, batch):
        """Persist a batch with a limited retry policy."""

        for attempt in range(self.max_retries):
            try:
                self.ledger.insert_trades(batch)

                self.persisted_count += len(batch)
                return

            except Exception as exc:
                if attempt == self.max_retries - 1:
                    self.error = exc
                    raise

                time.sleep(0.1 * (attempt + 1))

    def _run(self):
        """Consume queued trades and persist them in batches."""

        batch = []
        last_flush = time.monotonic()

        try:
            while True:
                try:
                    trade = self.trade_queue.get(
                        timeout=0.1
                    )

                    batch.append(trade)

                except queue.Empty:
                    pass

                should_flush = (
                    len(batch) >= self.batch_size
                    or (
                        batch
                        and time.monotonic() - last_flush
                        >= self.flush_interval
                    )
                )

                if should_flush:
                    self._save_batch(batch)

                    batch.clear()
                    last_flush = time.monotonic()

                if (
                    self.stop_event.is_set()
                    and self.trade_queue.empty()
                ):
                    break

            # Persist any remaining trades during shutdown.
            if batch:
                self._save_batch(batch)
                batch.clear()

        except Exception as exc:
            self.error = self.error or exc
            self.stop_event.set()

            # Count trades that could not be persisted.
            self.failed_count += len(batch)
            self.failed_count += self.trade_queue.qsize()

            batch.clear()

    def close(self):
        """Stop the worker and flush pending trades."""

        with self._lock:
            if self.closed:
                if self.error is not None:
                    raise RuntimeError(
                        "Trade writer failed; persistence is incomplete"
                    ) from self.error
                return

            self.closed = True
            self.stop_event.set()

        if self.worker is not None:
            self.worker.join()

        if self.error is not None:
            raise RuntimeError(
                "Trade writer failed; some trades may not be persisted"
            ) from self.error
