
# ChronosMatch — Week 1 

## Project Overview

ChronosMatch is a low-latency trading system prototype. Week 1 focuses on fixed-size binary order storage, a memory-mapped ring buffer, and an asynchronous mock market-data producer and consumer.

## 1. Memory-Mapped Ring Buffer

**Implementation:** `ipc/ring_buffer.py`

Technologies:
- Python `mmap` for memory-mapped file storage
- Python `struct` for fixed-size binary order records
- FIFO order processing
- Ring-buffer capacity and wraparound handling
- Buffer-full and buffer-empty exceptions

Each order contains:
- Order ID
- Price
- Quantity
- Side (BUY or SELL)

## 2. Ring Buffer Tests

**Test file:** `tests/test_ring_buffer.py`

Result: 5 tests passed.

Tests cover:
- Writing and reading an order
- Full-buffer handling
- Empty-buffer handling
- Ring-buffer wraparound
- FIFO ordering

## 3. Async Market-Data Firehose

**Implementation:** `market_simulator/firehose.py`

The firehose generates mock BUY and SELL orders and passes them through the ring buffer. It reports produced orders, consumed orders, elapsed time, throughput, and order losses.

## 4. Benchmark Results

**Benchmark file:** `benchmarks/benchmark_firehose.py`

| Metric | Result |
|---|---:|
| Target orders | 100,000 |
| Orders produced | 100,000 |
| Orders consumed | 100,000 |
| Elapsed time | 0.3449 seconds |
| Measured throughput | 289,923.56 orders/second |
| Target of 100,000 orders/second | Achieved |
| Orders lost | 0 |

The measured throughput exceeded the target by approximately 2.90 times in this run. Results are specific to the test environment and workload.

## 5. How to Run

Run commands from the project root.

Run the unit tests:

  powershell
python -m unittest discover -s tests -v


Run a small firehose test:

powershell
python -m market_simulator.firehose --orders 10000


Run the full benchmark:

powershell
python -m benchmarks.benchmark_firehose --orders 100000


## 6. Current Limitations

- The current ring-buffer lock coordinates threads sharing one buffer instance; it does not provide cross-process synchronization.
- The benchmark runs its producer and consumer in one process.
- The reported throughput is a prototype benchmark, not a guarantee of production trading performance.
- Cross-process synchronization, concurrency stress tests, and integration with a Cython matching engine remain future improvements.

## Week 1 Summary

The initial ring buffer implementation passed five unit tests. The 100,000-order benchmark completed with all orders consumed and zero reported order losses, achieving a measured throughput of 289,923.56 orders per second.
