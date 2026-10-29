# ChronosMatch – Week 3 Performance Report

## Objective

Optimize the Cython matching engine using C-level operations and implement nanosecond-level order-processing latency measurements.

## Completed Features

- Implemented a C-level matching function using Cython.
- Reduced Python-level operations during quantity updates.
- Used `nogil` sections for selected matching operations.
- Implemented nanosecond-level latency tracking using `time.perf_counter_ns()`.
- Added average, minimum, maximum, P50, P95, and P99 latency reporting.
- Integrated latency metrics into the matching-engine benchmark.

## Performance Comparison

| Metric | Week 2 | Week 3 |
|---|---:|---:|
| Orders Processed | 100,000 | 100,000 |
| Trades Executed | 77,953 | 77,953 |
| Execution Time | 1.8093 s | 1.6971 s |
| Throughput | 55,269.91 orders/sec | 58,925.23 orders/sec |
| Average Latency | 16.18 µs | 15.10 µs |
| P50 Latency | 12.30 µs | 11.70 µs |
| P95 Latency | 44.90 µs | 41.00 µs |
| P99 Latency | 79.30 µs | 71.30 µs |

## Nanosecond Latency Results

- Orders measured: 100,000
- Average latency: 15,100.60 ns
- Minimum latency: 200 ns
- Maximum latency: 2,202,200 ns
- P50 latency: 11,700 ns
- P95 latency: 41,000 ns
- P99 latency: 71,300 ns

## Testing

The existing automated test suite passed all 15 tests following the C-level matching changes. Nanosecond latency tracking was also exercised with a 100-order sample and a 100,000-order benchmark.

## Conclusion

The latest Week 3 benchmark demonstrated approximately 6.6% higher throughput and 6.7% lower average latency than the recorded Week 2 baseline.

The results are preliminary because they come from individual benchmark runs and may be affected by measurement overhead and system variability.

Further optimization and repeated benchmarking are recommended before making definitive performance claims.