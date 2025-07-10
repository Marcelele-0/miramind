import os
import sys
import threading
import time
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.miramind.llm.langgraph.performance_monitor import (
    PerformanceMonitor,
    get_performance_monitor,
    performance_monitor,
)


class TestPerformanceMonitor:
    """Test suite for PerformanceMonitor class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.monitor = PerformanceMonitor()

    def test_performance_monitor_initialization(self):
        """Test PerformanceMonitor initialization."""
        assert self.monitor.metrics == {}
        assert self.monitor.start_times == {}
        assert self.monitor.lock is not None

    @patch('time.time')
    @patch('psutil.Process')
    def test_track_operation_context_manager(self, mock_process, mock_time):
        """Test track_operation context manager."""
        # Mock time progression
        mock_time.side_effect = [1000.0, 1001.5]  # 1.5 second duration

        # Mock memory usage
        mock_memory_info = Mock()
        mock_memory_info.rss = 50 * 1024 * 1024  # 50MB start, 55MB end
        mock_process.return_value.memory_info.side_effect = [
            mock_memory_info,
            type('MockMemoryInfo', (), {'rss': 55 * 1024 * 1024})(),
        ]

        # Track an operation
        with self.monitor.track_operation("test_operation"):
            pass

        # Check metrics were recorded
        assert "test_operation" in self.monitor.metrics
        assert len(self.monitor.metrics["test_operation"]) == 1

        metric = self.monitor.metrics["test_operation"][0]
        assert metric["duration"] == 1.5
        assert metric["memory_delta"] == 5.0  # 5MB increase
        assert metric["timestamp"] == 1000.0

    @patch('time.time')
    @patch('psutil.Process')
    def test_track_operation_multiple_calls(self, mock_process, mock_time):
        """Test tracking multiple operations."""
        # Mock time progression for multiple operations
        mock_time.side_effect = [1000.0, 1001.0, 1002.0, 1003.0]  # Two 1-second operations

        # Mock memory usage
        mock_memory_info = Mock()
        mock_memory_info.rss = 50 * 1024 * 1024
        mock_process.return_value.memory_info.return_value = mock_memory_info

        # Track two operations
        with self.monitor.track_operation("test_op"):
            pass

        with self.monitor.track_operation("test_op"):
            pass

        # Check both operations were recorded
        assert len(self.monitor.metrics["test_op"]) == 2
        assert self.monitor.metrics["test_op"][0]["duration"] == 1.0
        assert self.monitor.metrics["test_op"][1]["duration"] == 1.0

    @patch('time.time')
    @patch('psutil.Process')
    def test_track_operation_with_exception(self, mock_process, mock_time):
        """Test tracking operation when exception occurs."""
        mock_time.side_effect = [1000.0, 1001.0]

        mock_memory_info = Mock()
        mock_memory_info.rss = 50 * 1024 * 1024
        mock_process.return_value.memory_info.return_value = mock_memory_info

        # Track operation that raises exception
        with pytest.raises(ValueError):
            with self.monitor.track_operation("error_operation"):
                raise ValueError("Test error")

        # Metrics should still be recorded
        assert "error_operation" in self.monitor.metrics
        assert len(self.monitor.metrics["error_operation"]) == 1

    def test_get_stats_single_operation(self):
        """Test get_stats for a single operation."""
        # Manually add some test data
        self.monitor.metrics["test_op"] = [
            {"duration": 1.0, "memory_delta": 2.0, "timestamp": 1000.0},
            {"duration": 2.0, "memory_delta": 3.0, "timestamp": 1001.0},
            {"duration": 3.0, "memory_delta": 1.0, "timestamp": 1002.0},
        ]

        stats = self.monitor.get_stats("test_op")

        assert stats["operation"] == "test_op"
        assert stats["count"] == 3
        assert stats["avg_duration"] == 2.0  # (1+2+3)/3
        assert stats["min_duration"] == 1.0
        assert stats["max_duration"] == 3.0
        assert stats["total_duration"] == 6.0

    def test_get_stats_nonexistent_operation(self):
        """Test get_stats for non-existent operation."""
        stats = self.monitor.get_stats("nonexistent")
        assert stats == {}

    def test_get_stats_all_operations(self):
        """Test get_stats for all operations."""
        # Add test data for multiple operations
        self.monitor.metrics["op1"] = [{"duration": 1.0, "memory_delta": 1.0, "timestamp": 1000.0}]
        self.monitor.metrics["op2"] = [{"duration": 2.0, "memory_delta": 2.0, "timestamp": 1001.0}]

        stats = self.monitor.get_stats()

        assert "op1" in stats
        assert "op2" in stats
        assert stats["op1"]["count"] == 1
        assert stats["op2"]["count"] == 1

    @patch('builtins.print')
    def test_print_stats(self, mock_print):
        """Test print_stats method."""
        # Add test data
        self.monitor.metrics["test_op"] = [
            {"duration": 1.5, "memory_delta": 2.0, "timestamp": 1000.0}
        ]

        self.monitor.print_stats()

        # Check that print was called with expected content
        mock_print.assert_called()
        print_calls = [call.args[0] for call in mock_print.call_args_list]

        # Check for expected content in print output
        assert any("PERFORMANCE STATISTICS" in call for call in print_calls)
        assert any("TEST_OP:" in call for call in print_calls)
        assert any("Count: 1" in call for call in print_calls)
        assert any("1.500s" in call for call in print_calls)

    def test_clear_stats(self):
        """Test clear_stats method."""
        # Add test data
        self.monitor.metrics["test_op"] = [
            {"duration": 1.0, "memory_delta": 1.0, "timestamp": 1000.0}
        ]

        assert len(self.monitor.metrics) == 1

        self.monitor.clear_stats()

        assert len(self.monitor.metrics) == 0

    def test_thread_safety(self):
        """Test thread safety of the performance monitor."""
        results = []

        def worker(monitor, worker_id):
            with monitor.track_operation(f"worker_{worker_id}"):
                time.sleep(0.01)  # Small delay to ensure timing
                results.append(worker_id)

        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(self.monitor, i))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check that all operations were tracked
        assert len(results) == 5

        # Check that all worker operations were recorded
        for i in range(5):
            assert f"worker_{i}" in self.monitor.metrics
            assert len(self.monitor.metrics[f"worker_{i}"]) == 1

    def test_get_performance_monitor_singleton(self):
        """Test get_performance_monitor returns singleton instance."""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()

        assert monitor1 is monitor2
        assert monitor1 is performance_monitor

    @patch('time.time')
    @patch('psutil.Process')
    def test_memory_calculation(self, mock_process, mock_time):
        """Test memory delta calculation."""
        mock_time.side_effect = [1000.0, 1001.0]

        # Mock memory info with different values
        start_memory = Mock()
        start_memory.rss = 100 * 1024 * 1024  # 100MB

        end_memory = Mock()
        end_memory.rss = 120 * 1024 * 1024  # 120MB

        mock_process.return_value.memory_info.side_effect = [start_memory, end_memory]

        with self.monitor.track_operation("memory_test"):
            pass

        metric = self.monitor.metrics["memory_test"][0]
        assert metric["memory_delta"] == 20.0  # 20MB increase

    @patch('time.time')
    @patch('psutil.Process')
    def test_negative_memory_delta(self, mock_process, mock_time):
        """Test handling of negative memory delta."""
        mock_time.side_effect = [1000.0, 1001.0]

        # Mock memory decrease
        start_memory = Mock()
        start_memory.rss = 100 * 1024 * 1024  # 100MB

        end_memory = Mock()
        end_memory.rss = 80 * 1024 * 1024  # 80MB

        mock_process.return_value.memory_info.side_effect = [start_memory, end_memory]

        with self.monitor.track_operation("memory_decrease"):
            pass

        metric = self.monitor.metrics["memory_decrease"][0]
        assert metric["memory_delta"] == -20.0  # 20MB decrease

    def test_stats_with_empty_metrics(self):
        """Test stats calculation with empty metrics."""
        stats = self.monitor.get_stats("empty_op")
        assert stats == {}

        all_stats = self.monitor.get_stats()
        assert all_stats == {}

    @patch('builtins.print')
    def test_print_stats_empty(self, mock_print):
        """Test print_stats with no metrics."""
        self.monitor.print_stats()

        # Should still print headers
        mock_print.assert_called()
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        assert any("PERFORMANCE STATISTICS" in call for call in print_calls)

    def test_multiple_operations_different_names(self):
        """Test tracking multiple operations with different names."""
        # Manually add test data
        self.monitor.metrics["fast_op"] = [
            {"duration": 0.1, "memory_delta": 1.0, "timestamp": 1000.0}
        ]
        self.monitor.metrics["slow_op"] = [
            {"duration": 2.0, "memory_delta": 5.0, "timestamp": 1001.0}
        ]

        fast_stats = self.monitor.get_stats("fast_op")
        slow_stats = self.monitor.get_stats("slow_op")

        assert fast_stats["avg_duration"] == 0.1
        assert slow_stats["avg_duration"] == 2.0
        assert fast_stats["count"] == 1
        assert slow_stats["count"] == 1
