
"""Memory-mapped ring buffer for fixed-size trading orders."""

import mmap
import os
import struct
import threading
from pathlib import Path


# Header: write position, read position
HEADER = struct.Struct("<QQ")

# Record: order_id, price, quantity, side, padding
# side: 0 = BUY, 1 = SELL
RECORD = struct.Struct("<QdIB3x")


class BufferFull(Exception):
    """Raised when the ring buffer has no free slots."""


class BufferEmpty(Exception):
    """Raised when the ring buffer contains no orders."""


class RingBuffer:
    """File-backed mmap ring buffer for a single process."""

    def __init__(self, path, capacity=1024):
        if capacity < 1:
            raise ValueError("capacity must be at least 1")

        self.capacity = capacity
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self._file = open(self.path, "a+b")

        expected_size = HEADER.size + capacity * RECORD.size
        self._file.seek(0, os.SEEK_END)
        current_size = self._file.tell()

        if current_size == 0:
            self._file.truncate(expected_size)
            self._file.flush()
            self._file.seek(0)
            self._file.write(HEADER.pack(0, 0))
            self._file.flush()
        elif current_size != expected_size:
            self._file.close()
            raise ValueError(
                f"Existing buffer size is {current_size}; "
                f"expected {expected_size}. Use a new file or "
                "reinitialize the buffer."
            )

        self._map = mmap.mmap(self._file.fileno(), 0)

    def put(self, order_id, price, quantity, side):
        """Write one order; reject writes when the buffer is full."""
        if side not in ("BUY", "SELL"):
            raise ValueError("side must be BUY or SELL")

        if not 0 <= order_id <= 0xFFFFFFFFFFFFFFFF:
            raise ValueError("order_id must fit in an unsigned 64-bit integer")

        if not 0 <= quantity <= 0xFFFFFFFF:
            raise ValueError("quantity must fit in an unsigned 32-bit integer")

        if price < 0:
            raise ValueError("price must be non-negative")

        side_code = 0 if side == "BUY" else 1
        record = RECORD.pack(
            order_id, price, quantity, side_code
        )

        with self._lock:
            write_pos, read_pos = HEADER.unpack_from(self._map, 0)

            if write_pos - read_pos >= self.capacity:
                raise BufferFull("Ring buffer is full")

            slot = write_pos % self.capacity
            offset = HEADER.size + slot * RECORD.size

            self._map[offset:offset + RECORD.size] = record
            HEADER.pack_into(
                self._map, 0, write_pos + 1, read_pos
            )

    def get(self):
        """Read and remove the oldest order."""
        with self._lock:
            write_pos, read_pos = HEADER.unpack_from(self._map, 0)

            if write_pos == read_pos:
                raise BufferEmpty("Ring buffer is empty")

            slot = read_pos % self.capacity
            offset = HEADER.size + slot * RECORD.size

            order_id, price, quantity, side_code = (
                RECORD.unpack_from(self._map, offset)
            )

            HEADER.pack_into(
                self._map, 0, write_pos, read_pos + 1
            )

            return {
                "order_id": order_id,
                "price": price,
                "quantity": quantity,
                "side": "BUY" if side_code == 0 else "SELL",
            }

    def __len__(self):
        with self._lock:
            write_pos, read_pos = HEADER.unpack_from(self._map, 0)
            return write_pos - read_pos

    def close(self):
        """Flush and release mapped memory and the file."""
        if not self._map.closed:
            self._map.flush()
            self._map.close()

        if not self._file.closed:
            self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
