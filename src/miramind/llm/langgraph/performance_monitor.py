import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from typing import Dict, List

import psutil


class PerformanceMonitor:
    """Monitor and track performance metrics for the chatbot."""

    def __init__(self):
        self.metrics = defaultdict(list)
        self.start_times = {}
        self.lock = threading.Lock()

    @contextmanager
    def track_operation(self, operation_name: str):
        """Context manager to track operation timing."""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        try:
            yield
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

            duration = end_time - start_time
            memory_delta = end_memory - start_memory

            with self.lock:
                self.metrics[operation_name].append(
                    {'duration': duration, 'memory_delta': memory_delta, 'timestamp': start_time}
                )

    def get_stats(self, operation_name: str = None) -> Dict:
        """Get performance statistics."""
        with self.lock:
            if operation_name:
                data = self.metrics.get(operation_name, [])
                if not data:
                    return {}

                durations = [d['duration'] for d in data]
                return {
                    'operation': operation_name,
                    'count': len(data),
                    'avg_duration': sum(durations) / len(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations),
                    'total_duration': sum(durations),
                }
            else:
                # Return stats for all operations
                stats = {}
                for op_name in self.metrics:
                    stats[op_name] = self.get_stats(op_name)
                return stats

    def print_stats(self):
        """Print performance statistics to console."""
        stats = self.get_stats()
        print("\n" + "=" * 50)
        print("PERFORMANCE STATISTICS")
        print("=" * 50)

        for op_name, data in stats.items():
            if data:
                print(f"\n{op_name.upper()}:")
                print(f"  Count: {data['count']}")
                print(f"  Avg Duration: {data['avg_duration']:.3f}s")
                print(f"  Min Duration: {data['min_duration']:.3f}s")
                print(f"  Max Duration: {data['max_duration']:.3f}s")
                print(f"  Total Duration: {data['total_duration']:.3f}s")

    def clear_stats(self):
        """Clear all performance statistics."""
        with self.lock:
            self.metrics.clear()


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def get_performance_monitor():
    """Get the global performance monitor instance."""
    return performance_monitor
