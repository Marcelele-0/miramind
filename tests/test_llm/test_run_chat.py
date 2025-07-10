import hashlib
import json
import os
import sys
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.miramind.llm.langgraph.run_chat import (
    OUTPUT_AUDIO_PATH,
    _hash_input,
    executor,
    perf_monitor,
    process_chat_message,
    response_cache,
)


class TestRunChat:
    """Test suite for run_chat module."""

    def setup_method(self):
        """Setup test fixtures."""
        # Clear cache before each test
        response_cache.clear()

        # Mock chatbot
        self.mock_chatbot = Mock()
        self.mock_result = {
            "response": "Test response",
            "response_audio": b"test_audio_data",
            "chat_history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Test response"},
            ],
        }
        self.mock_chatbot.invoke.return_value = self.mock_result

    def test_hash_input_basic(self):
        """Test _hash_input function with basic input."""
        input_text = "Hello world"
        hash_result = _hash_input(input_text)

        # Should be a valid MD5 hash
        assert len(hash_result) == 32
        assert all(c in '0123456789abcdef' for c in hash_result)

        # Same input should produce same hash
        assert _hash_input(input_text) == hash_result

    def test_hash_input_with_emotion(self):
        """Test _hash_input function with emotion parameter."""
        input_text = "Hello world"
        hash_without_emotion = _hash_input(input_text)
        hash_with_emotion = _hash_input(input_text, "happy")

        # Different emotions should produce different hashes
        assert hash_without_emotion != hash_with_emotion

    def test_hash_input_case_insensitive(self):
        """Test _hash_input is case insensitive."""
        hash1 = _hash_input("Hello World")
        hash2 = _hash_input("hello world")

        assert hash1 == hash2

    def test_hash_input_strips_whitespace(self):
        """Test _hash_input strips whitespace."""
        hash1 = _hash_input("  hello world  ")
        hash2 = _hash_input("hello world")

        assert hash1 == hash2

    def test_output_audio_path_exists(self):
        """Test that OUTPUT_AUDIO_PATH is properly constructed."""
        assert OUTPUT_AUDIO_PATH is not None
        assert "frontend" in OUTPUT_AUDIO_PATH
        assert "public" in OUTPUT_AUDIO_PATH
        assert "output.wav" in OUTPUT_AUDIO_PATH
        assert os.path.isabs(OUTPUT_AUDIO_PATH)

    @patch('src.miramind.llm.langgraph.run_chat.chatbot')
    @patch('builtins.open', new_callable=mock_open)
    def test_process_chat_message_basic(self, mock_file, mock_chatbot):
        """Test basic chat message processing."""
        mock_chatbot.invoke.return_value = self.mock_result

        result = process_chat_message("Hello, how are you?")

        # Check that chatbot was called with correct state
        mock_chatbot.invoke.assert_called_once()
        call_args = mock_chatbot.invoke.call_args[0][0]

        assert call_args["user_input"] == "Hello, how are you?"
        assert call_args["chat_history"] == []
        assert call_args["memory"] == ""

        # Check return value
        assert result == self.mock_result

    @patch('src.miramind.llm.langgraph.run_chat.chatbot')
    @patch('builtins.open', new_callable=mock_open)
    def test_process_chat_message_with_history(self, mock_file, mock_chatbot):
        """Test chat message processing with chat history."""
        mock_chatbot.invoke.return_value = self.mock_result

        chat_history = [
            {"role": "user", "content": "Previous message"},
            {"role": "assistant", "content": "Previous response"},
        ]

        result = process_chat_message("New message", chat_history=chat_history)

        # Check that chat history was passed correctly
        call_args = mock_chatbot.invoke.call_args[0][0]
        assert call_args["chat_history"] == chat_history

    @patch('src.miramind.llm.langgraph.run_chat.chatbot')
    @patch('builtins.open', new_callable=mock_open)
    def test_process_chat_message_with_memory(self, mock_file, mock_chatbot):
        """Test chat message processing with memory."""
        mock_chatbot.invoke.return_value = self.mock_result

        result = process_chat_message("Hello", memory="Previous context")

        # Check that memory was passed correctly
        call_args = mock_chatbot.invoke.call_args[0][0]
        assert call_args["memory"] == "Previous context"

    @patch('src.miramind.llm.langgraph.run_chat.chatbot')
    @patch('builtins.open', new_callable=mock_open)
    def test_process_chat_message_audio_saving(self, mock_file, mock_chatbot):
        """Test that audio is saved when present."""
        mock_chatbot.invoke.return_value = self.mock_result

        result = process_chat_message("Hello")

        # Check that file was opened for writing
        mock_file.assert_called_once_with(OUTPUT_AUDIO_PATH, "wb")

        # Check that audio data was written
        handle = mock_file.return_value.__enter__.return_value
        handle.write.assert_called_once_with(b"test_audio_data")

    @patch('src.miramind.llm.langgraph.run_chat.chatbot')
    @patch('builtins.open', new_callable=mock_open)
    def test_process_chat_message_no_audio(self, mock_file, mock_chatbot):
        """Test processing when no audio is present."""
        result_no_audio = {"response": "Test response", "response_audio": None, "chat_history": []}
        mock_chatbot.invoke.return_value = result_no_audio

        result = process_chat_message("Hello")

        # File should not be opened when no audio
        mock_file.assert_not_called()

    @patch('src.miramind.llm.langgraph.run_chat.chatbot')
    @patch('builtins.open', side_effect=IOError("File write error"))
    def test_process_chat_message_audio_save_error(self, mock_file, mock_chatbot):
        """Test handling of audio save errors."""
        mock_chatbot.invoke.return_value = self.mock_result

        # Should not raise exception even if file write fails
        result = process_chat_message("Hello")

        # Should still return the result
        assert result == self.mock_result

    @patch('src.miramind.llm.langgraph.run_chat.chatbot')
    @patch('builtins.open', new_callable=mock_open)
    def test_process_chat_message_caching(self, mock_file, mock_chatbot):
        """Test response caching functionality."""
        mock_chatbot.invoke.return_value = self.mock_result

        # First call should invoke chatbot
        result1 = process_chat_message("Hello")
        assert mock_chatbot.invoke.call_count == 1

        # Second call with same input should use cache
        result2 = process_chat_message("Hello")
        assert mock_chatbot.invoke.call_count == 1  # Should not increase

        # Results should be the same
        assert result1 == result2

    @patch('src.miramind.llm.langgraph.run_chat.chatbot')
    @patch('builtins.open', new_callable=mock_open)
    def test_process_chat_message_cache_different_inputs(self, mock_file, mock_chatbot):
        """Test that different inputs don't use cached results."""
        mock_chatbot.invoke.return_value = self.mock_result

        # Different inputs should invoke chatbot separately
        result1 = process_chat_message("Hello")
        result2 = process_chat_message("Goodbye")

        assert mock_chatbot.invoke.call_count == 2

    @patch('src.miramind.llm.langgraph.run_chat.chatbot')
    @patch('builtins.open', new_callable=mock_open)
    def test_process_chat_message_performance_monitoring(self, mock_file, mock_chatbot):
        """Test that performance monitoring is used."""
        mock_chatbot.invoke.return_value = self.mock_result

        # Clear any existing metrics
        perf_monitor.clear_stats()

        result = process_chat_message("Hello")

        # Check that performance metrics were recorded
        stats = perf_monitor.get_stats()
        assert "total_chat_processing" in stats
        assert "cache_lookup" in stats

    @patch('src.miramind.llm.langgraph.run_chat.chatbot')
    @patch('builtins.open', new_callable=mock_open)
    def test_process_chat_message_chatbot_error(self, mock_file, mock_chatbot):
        """Test handling of chatbot errors."""
        mock_chatbot.invoke.side_effect = Exception("Chatbot error")

        # Should raise the exception
        with pytest.raises(Exception, match="Chatbot error"):
            process_chat_message("Hello")

    @patch('src.miramind.llm.langgraph.run_chat.chatbot')
    @patch('builtins.open', new_callable=mock_open)
    def test_process_chat_message_state_construction(self, mock_file, mock_chatbot):
        """Test that state is properly constructed."""
        mock_chatbot.invoke.return_value = self.mock_result

        chat_history = [{"role": "user", "content": "Hi"}]
        memory = "Context"

        process_chat_message("Hello", chat_history=chat_history, memory=memory)

        # Check state construction
        call_args = mock_chatbot.invoke.call_args[0][0]

        assert call_args["user_input"] == "Hello"
        assert call_args["chat_history"] == chat_history
        assert call_args["memory"] == memory

    def test_response_cache_global_state(self):
        """Test that response cache is properly maintained globally."""
        # Cache should be empty initially
        assert len(response_cache) == 0

        # Add something to cache
        test_key = "test_key"
        test_value = {"response": "cached"}
        response_cache[test_key] = test_value

        assert len(response_cache) == 1
        assert response_cache[test_key] == test_value

    def test_executor_exists(self):
        """Test that thread pool executor exists."""
        assert executor is not None
        assert hasattr(executor, 'submit')
        assert hasattr(executor, 'shutdown')

    def test_perf_monitor_exists(self):
        """Test that performance monitor exists."""
        assert perf_monitor is not None
        assert hasattr(perf_monitor, 'track_operation')
        assert hasattr(perf_monitor, 'get_stats')

    @patch('src.miramind.llm.langgraph.run_chat.chatbot')
    @patch('builtins.open', new_callable=mock_open)
    def test_process_chat_message_return_structure(self, mock_file, mock_chatbot):
        """Test that return structure matches expected format."""
        mock_chatbot.invoke.return_value = self.mock_result

        result = process_chat_message("Hello")

        # Check that all expected fields are present
        assert "response" in result
        assert "response_audio" in result
        assert "chat_history" in result

        # Check types
        assert isinstance(result["response"], str)
        assert isinstance(result["response_audio"], bytes)
        assert isinstance(result["chat_history"], list)

    @patch('src.miramind.llm.langgraph.run_chat.chatbot')
    @patch('builtins.open', new_callable=mock_open)
    def test_process_chat_message_empty_input(self, mock_file, mock_chatbot):
        """Test processing with empty input."""
        mock_chatbot.invoke.return_value = self.mock_result

        result = process_chat_message("")

        # Should still process empty input
        call_args = mock_chatbot.invoke.call_args[0][0]
        assert call_args["user_input"] == ""

    @patch('src.miramind.llm.langgraph.run_chat.chatbot')
    @patch('builtins.open', new_callable=mock_open)
    def test_process_chat_message_unicode_input(self, mock_file, mock_chatbot):
        """Test processing with unicode input."""
        mock_chatbot.invoke.return_value = self.mock_result

        unicode_input = "Hello 你好 🌟"
        result = process_chat_message(unicode_input)

        # Should handle unicode correctly
        call_args = mock_chatbot.invoke.call_args[0][0]
        assert call_args["user_input"] == unicode_input

    def test_cache_key_consistency(self):
        """Test that cache keys are consistent."""
        input_text = "Hello world"

        # Same input should always produce same key
        key1 = _hash_input(input_text)
        key2 = _hash_input(input_text)

        assert key1 == key2

        # Different inputs should produce different keys
        key3 = _hash_input("Different input")
        assert key1 != key3
