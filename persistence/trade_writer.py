
import queue
import threading
import time


class TradeWriter:
    def __init__(
        self,
        ledger,
        batch_size=100,
        flush_interval=1.0,
        max_retries=3
    ):
        self.ledger = ledger
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_retries = max_retries

        self.trade_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.worker = threading.Thread(
            target=self._run,
            name="TradeWriter",
            daemon=True
        )

        self.error = None
        self.started = False

    def start(self):
        if self.started:
            return

        self.started = True
        self.worker.start()

    def submit(self, trade):
        if not self.started or self.stop_event.is_set():
            raise RuntimeError("Trade writer is not accepting trades")

        self.trade_queue.put(trade)

    def _save_batch(self, batch):
        for attempt in range(self.max_retries):
            try:
                self.ledger.insert_trades(batch)
                return
            except Exception as exc:
                if attempt == self.max_retries - 1:
                    self.error = exc
                    raise

                time.sleep(0.1 * (attempt + 1))

    def _run(self):
        batch = []
        last_flush = time.monotonic()

        while True:
            try:
                trade = self.trade_queue.get(timeout=0.1)
                if trade is not None:
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
                try:
                    self._save_batch(batch)
                    batch.clear()
                    last_flush = time.monotonic()
                except Exception:
                    self.stop_event.set()
                    break

            if self.stop_event.is_set() and self.trade_queue.empty():
                break

        if batch:
            try:
                self._save_batch(batch)
            except Exception:
                self.error = self.error or RuntimeError(
                    "Final batch could not be persisted"
                )

    def close(self):
        if not self.started:
            return

        self.stop_event.set()
        self.worker.join()

        if self.error:
            raise RuntimeError(
                "Trade writer failed; some trades may not be persisted"
            ) from self.error

        self.started = False
