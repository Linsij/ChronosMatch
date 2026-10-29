
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


## Week 2 — Cython Matching Engine and Latency Dashboard

### 1. Cython Limit Order Book

Implemented a Limit Order Book using Cython in `matching_engine/order_book.pyx`.

Features:
- BUY and SELL order matching
- Price-time priority
- Exact matches and partial fills
- Multiple trade executions
- Fixed-size C structures for resting orders
- Integer-based price representation
- GIL-free best-price search sections using `nogil`

The matching operation as a whole is not yet GIL-free.

### 2. Matching Engine Testing

Implemented 10 automated matching-engine tests covering order insertion, exact matching, partial fills, price priority, time priority, multiple matches, unmatched orders, and invalid inputs.

Results:
- Week 1 tests: 5 passed
- Week 2 tests: 10 passed
- Total: 15 passed

### 3. Real-Time Terminal Dashboard

Implemented `dashboard/latency_dashboard.py` using Python `curses`.

The dashboard displays:
- Best bid and ask prices
- Bid/ask spread
- Resting BUY and SELL order counts
- Executed trade count
- Last order-processing latency
- Simulated order-processing rate

The dashboard was tested successfully on Windows.

### 4. Matching Engine Benchmark

Benchmark file: `benchmarks/benchmark_matching.py`

| Metric | Result |
|---|---:|
| Orders processed | 100,000 |
| Trades executed | 77,953 |
| Elapsed time | 1.8093 seconds |
| Throughput | 55,269.91 orders/sec |
| Average latency | 16.18 µs |
| P50 latency | 12.30 µs |
| P95 latency | 44.90 µs |
| P99 latency | 79.30 µs |

The benchmark measures the Cython matching engine under a synthetic workload. Total elapsed time includes order generation and measurement overhead.

### 5. Running Week 2

Compile the matching engine:

`python setup.py build_ext --inplace`

Run all tests:

`python -m unittest discover -s tests -v`

Run the terminal dashboard:

`python -m dashboard.latency_dashboard`

Run the matching-engine benchmark:

`python -m benchmarks.benchmark_matching --orders 100000`

### 6. Current Limitations

- The complete matching operation does not run without the GIL.
- The engine uses linear scans to locate the best resting order.
- Cancellation, modification, and duplicate-order-ID handling are not yet implemented.
- The dashboard runs a simulated order stream rather than consuming the Week 1 shared-memory buffer.
- Additional stress testing and concurrency verification are required before production use.

### Week 2 Summary

Implemented and compiled a Cython-based Limit Order Book with price-time priority, validated it with 10 automated tests, and developed a real-time terminal dashboard.

The matching-engine benchmark processed 100,000 orders at 55,269.91 orders per second, with an average measured order-processing latency of 16.18 microseconds.

## Week 3 – C-Level Optimization and Metrics Tracking

### Completed Features

- Optimized matching operations using Cython C-level functions.
- Reduced Python-level interactions during order quantity updates.
- Implemented `nogil` sections for selected matching operations.
- Added nanosecond-level latency tracking using `time.perf_counter_ns()`.
- Integrated latency statistics into the benchmark.
- Added 3 automated latency tests.

### Performance Results

| Metric | Week 2 | Week 3 |
|---|---:|---:|
| Orders Processed | 100,000 | 100,000 |
| Trades Executed | 77,953 | 77,953 |
| Throughput | 55,269.91/s | 57,367.60/s |
| Average Latency | 16.18 µs | 15.48 µs |
| P99 Latency | 79.30 µs | 72.60 µs |

### Testing

All 18 automated tests passed.

### Week 3 Outcome

Implemented C-level matching improvements and nanosecond latency measurements. The latest benchmark recorded approximately 3.8% higher throughput compared with the Week 2 baseline.

The matching engine remains a prototype, and further benchmarking and optimization are recommended.