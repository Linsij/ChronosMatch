
"""Nanosecond-level order processing latency tracking."""

import statistics
import time


class LatencyMetrics:
    def __init__(self):
        self.latencies_ns = []

    def start(self):
        """Capture the order entry timestamp."""
        return time.perf_counter_ns()

    def stop(self, start_ns):
        """Capture the exit timestamp and record latency."""
        end_ns = time.perf_counter_ns()
        latency_ns = end_ns - start_ns
        self.latencies_ns.append(latency_ns)
        return latency_ns

    def summary(self):
        if not self.latencies_ns:
            return {
                "orders_measured": 0,
                "average_ns": 0,
                "min_ns": 0,
                "max_ns": 0,
                "p50_ns": 0,
                "p95_ns": 0,
                "p99_ns": 0,
            }

        values = sorted(self.latencies_ns)

        def percentile(p):
            index = int((len(values) - 1) * p)
            return values[index]

        return {
            "orders_measured": len(values),
            "average_ns": statistics.mean(values),
            "min_ns": values[0],
            "max_ns": values[-1],
            "p50_ns": percentile(0.50),
            "p95_ns": percentile(0.95),
            "p99_ns": percentile(0.99),
        }
