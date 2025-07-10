import json
import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.miramind.llm.langgraph.chatbot import get_chatbot
from src.miramind.llm.langgraph.performance_monitor import get_performance_monitor
from src.miramind.llm.langgraph.run_chat import process_chat_message
from src.miramind.llm.langgraph.utils import EmotionLogger, call_openai


class TestLLMIntegration:
    """Integration tests for the LLM/LangGraph system."""

    def setup_method(self):
        """Setup test fixtures."""
        # Clear performance monitor for clean tests
        get_performance_monitor().clear_stats()

    @patch('src.miramind.llm.langgraph.chatbot.initialize_clients')
    @patch('src.miramind.llm.langgraph.subgraphs.generate_response')
    @patch('src.miramind.llm.langgraph.chatbot.call_openai')
    def test_end_to_end_sad_emotion_flow(
        self, mock_call_openai, mock_generate_response, mock_init_clients
    ):
        """Test complete flow from input to response for sad emotion."""
        # Setup mocks
        mock_client = Mock()
        mock_tts_provider = Mock()
        mock_emotion_logger = Mock()
        mock_init_clients.return_value = (mock_client, mock_tts_provider, mock_emotion_logger)

        # Mock emotion detection
        mock_call_openai.return_value = '{"emotion": "sad", "confidence": 0.85}'

        # Mock response generation
        def mock_response_func(state):
            return {
                **state,
                "response": "I'm sorry to hear you're feeling sad. Would you like to tell me more about what's making you feel this way?",
                "response_audio": b"audio_data",
                "chat_history": state.get("chat_history", [])
                + [
                    {"role": "user", "content": state["user_input"]},
                    {"role": "assistant", "content": "I'm sorry to hear you're feeling sad."},
                ],
            }

        mock_generate_response.return_value = mock_response_func

        # Process message
        with (
            patch('src.miramind.llm.langgraph.chatbot.client', mock_client),
            patch('src.miramind.llm.langgraph.chatbot.tts_provider', mock_tts_provider),
            patch('src.miramind.llm.langgraph.chatbot.emotion_logger', mock_emotion_logger),
            patch('builtins.open', MagicMock()),
        ):

            result = process_chat_message("I'm feeling really sad today")

            # Verify the complete flow
            assert result["response"] is not None
            assert "sad" in result["response"].lower() or "sorry" in result["response"].lower()
            assert result["response_audio"] == b"audio_data"
            assert len(result["chat_history"]) >= 2

    @patch('src.miramind.llm.langgraph.chatbot.initialize_clients')
    @patch('src.miramind.llm.langgraph.subgraphs.generate_response')
    @patch('src.miramind.llm.langgraph.chatbot.call_openai')
    def test_end_to_end_happy_emotion_flow(
        self, mock_call_openai, mock_generate_response, mock_init_clients
    ):
        """Test complete flow for happy emotion."""
        # Setup mocks
        mock_client = Mock()
        mock_tts_provider = Mock()
        mock_emotion_logger = Mock()
        mock_init_clients.return_value = (mock_client, mock_tts_provider, mock_emotion_logger)

        # Mock emotion detection
        mock_call_openai.return_value = '{"emotion": "happy", "confidence": 0.92}'

        # Mock response generation
        def mock_response_func(state):
            return {
                **state,
                "response": "That's wonderful to hear! I'm so happy for you!",
                "response_audio": b"happy_audio_data",
                "chat_history": state.get("chat_history", [])
                + [
                    {"role": "user", "content": state["user_input"]},
                    {"role": "assistant", "content": "That's wonderful to hear!"},
                ],
            }

        mock_generate_response.return_value = mock_response_func

        # Process message
        with (
            patch('src.miramind.llm.langgraph.chatbot.client', mock_client),
            patch('src.miramind.llm.langgraph.chatbot.tts_provider', mock_tts_provider),
            patch('src.miramind.llm.langgraph.chatbot.emotion_logger', mock_emotion_logger),
            patch('builtins.open', MagicMock()),
        ):

            result = process_chat_message("I just got the best news ever!")

            # Verify happy response
            assert result["response"] is not None
            assert (
                "happy" in result["response"].lower() or "wonderful" in result["response"].lower()
            )

    @patch('src.miramind.llm.langgraph.chatbot.initialize_clients')
    @patch('src.miramind.llm.langgraph.subgraphs.generate_response')
    @patch('src.miramind.llm.langgraph.chatbot.call_openai')
    def test_conversation_with_chat_history(
        self, mock_call_openai, mock_generate_response, mock_init_clients
    ):
        """Test conversation flow with chat history."""
        # Setup mocks
        mock_client = Mock()
        mock_tts_provider = Mock()
        mock_emotion_logger = Mock()
        mock_init_clients.return_value = (mock_client, mock_tts_provider, mock_emotion_logger)

        # Mock emotion detection
        mock_call_openai.return_value = '{"emotion": "neutral", "confidence": 0.7}'

        # Mock response generation
        def mock_response_func(state):
            return {
                **state,
                "response": "I understand. How can I help you today?",
                "response_audio": b"neutral_audio_data",
                "chat_history": state.get("chat_history", [])
                + [
                    {"role": "user", "content": state["user_input"]},
                    {"role": "assistant", "content": "I understand. How can I help you today?"},
                ],
            }

        mock_generate_response.return_value = mock_response_func

        # Start conversation
        chat_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there! How are you feeling today?"},
        ]

        with (
            patch('src.miramind.llm.langgraph.chatbot.client', mock_client),
            patch('src.miramind.llm.langgraph.chatbot.tts_provider', mock_tts_provider),
            patch('src.miramind.llm.langgraph.chatbot.emotion_logger', mock_emotion_logger),
            patch('builtins.open', MagicMock()),
        ):

            result = process_chat_message("I'm doing okay", chat_history=chat_history)

            # Verify chat history is maintained and extended
            assert len(result["chat_history"]) > len(chat_history)
            assert result["chat_history"][-2]["role"] == "user"
            assert result["chat_history"][-1]["role"] == "assistant"

    @patch('src.miramind.llm.langgraph.chatbot.initialize_clients')
    @patch('src.miramind.llm.langgraph.subgraphs.generate_response')
    @patch('src.miramind.llm.langgraph.chatbot.call_openai')
    def test_emotion_detection_fallback(
        self, mock_call_openai, mock_generate_response, mock_init_clients
    ):
        """Test emotion detection fallback to neutral."""
        # Setup mocks
        mock_client = Mock()
        mock_tts_provider = Mock()
        mock_emotion_logger = Mock()
        mock_init_clients.return_value = (mock_client, mock_tts_provider, mock_emotion_logger)

        # Mock failed emotion detection
        mock_call_openai.return_value = "Invalid JSON response"

        # Mock response generation
        def mock_response_func(state):
            return {
                **state,
                "response": "I'm here to help you.",
                "response_audio": b"neutral_audio_data",
                "chat_history": state.get("chat_history", [])
                + [
                    {"role": "user", "content": state["user_input"]},
                    {"role": "assistant", "content": "I'm here to help you."},
                ],
            }

        mock_generate_response.return_value = mock_response_func

        with (
            patch('src.miramind.llm.langgraph.chatbot.client', mock_client),
            patch('src.miramind.llm.langgraph.chatbot.tts_provider', mock_tts_provider),
            patch('src.miramind.llm.langgraph.chatbot.emotion_logger', mock_emotion_logger),
            patch('builtins.open', MagicMock()),
        ):

            result = process_chat_message("Some unclear emotional message")

            # Should fallback to neutral flow
            assert result["response"] is not None

    @patch('src.miramind.llm.langgraph.chatbot.initialize_clients')
    @patch('src.miramind.llm.langgraph.subgraphs.generate_response')
    @patch('src.miramind.llm.langgraph.chatbot.call_openai')
    def test_performance_monitoring_integration(
        self, mock_call_openai, mock_generate_response, mock_init_clients
    ):
        """Test that performance monitoring works during chat processing."""
        # Setup mocks
        mock_client = Mock()
        mock_tts_provider = Mock()
        mock_emotion_logger = Mock()
        mock_init_clients.return_value = (mock_client, mock_tts_provider, mock_emotion_logger)

        # Mock responses
        mock_call_openai.return_value = '{"emotion": "happy", "confidence": 0.9}'

        def mock_response_func(state):
            return {
                **state,
                "response": "Great!",
                "response_audio": b"audio_data",
                "chat_history": [],
            }

        mock_generate_response.return_value = mock_response_func

        # Clear performance monitor
        perf_monitor = get_performance_monitor()
        perf_monitor.clear_stats()

        with (
            patch('src.miramind.llm.langgraph.chatbot.client', mock_client),
            patch('src.miramind.llm.langgraph.chatbot.tts_provider', mock_tts_provider),
            patch('src.miramind.llm.langgraph.chatbot.emotion_logger', mock_emotion_logger),
            patch('builtins.open', MagicMock()),
        ):

            result = process_chat_message("I'm happy!")

            # Check that performance metrics were recorded
            stats = perf_monitor.get_stats()
            assert "total_chat_processing" in stats
            assert "cache_lookup" in stats

    @patch('src.miramind.llm.langgraph.chatbot.initialize_clients')
    @patch('src.miramind.llm.langgraph.subgraphs.generate_response')
    @patch('src.miramind.llm.langgraph.chatbot.call_openai')
    def test_emotion_logging_integration(
        self, mock_call_openai, mock_generate_response, mock_init_clients
    ):
        """Test that emotions are properly logged during processing."""
        # Setup mocks
        mock_client = Mock()
        mock_tts_provider = Mock()
        mock_emotion_logger = Mock()
        mock_init_clients.return_value = (mock_client, mock_tts_provider, mock_emotion_logger)

        # Mock responses
        mock_call_openai.return_value = '{"emotion": "angry", "confidence": 0.8}'

        def mock_response_func(state):
            return {
                **state,
                "response": "I understand you're feeling angry.",
                "response_audio": b"audio_data",
                "chat_history": [],
            }

        mock_generate_response.return_value = mock_response_func

        with (
            patch('src.miramind.llm.langgraph.chatbot.client', mock_client),
            patch('src.miramind.llm.langgraph.chatbot.tts_provider', mock_tts_provider),
            patch('src.miramind.llm.langgraph.chatbot.emotion_logger', mock_emotion_logger),
            patch('builtins.open', MagicMock()),
        ):

            result = process_chat_message("I'm so frustrated!")

            # Verify logging was called (note: actual logging happens in generate_response)
            # This test verifies the integration works without errors
            assert result["response"] is not None

    @patch('src.miramind.llm.langgraph.chatbot.initialize_clients')
    @patch('src.miramind.llm.langgraph.subgraphs.generate_response')
    @patch('src.miramind.llm.langgraph.chatbot.call_openai')
    def test_tts_integration(self, mock_call_openai, mock_generate_response, mock_init_clients):
        """Test TTS integration in the complete flow."""
        # Setup mocks
        mock_client = Mock()
        mock_tts_provider = Mock()
        mock_emotion_logger = Mock()
        mock_init_clients.return_value = (mock_client, mock_tts_provider, mock_emotion_logger)

        # Mock responses
        mock_call_openai.return_value = '{"emotion": "excited", "confidence": 0.95}'

        def mock_response_func(state):
            return {
                **state,
                "response": "That's amazing!",
                "response_audio": b"excited_audio_data",
                "chat_history": [],
            }

        mock_generate_response.return_value = mock_response_func

        with (
            patch('src.miramind.llm.langgraph.chatbot.client', mock_client),
            patch('src.miramind.llm.langgraph.chatbot.tts_provider', mock_tts_provider),
            patch('src.miramind.llm.langgraph.chatbot.emotion_logger', mock_emotion_logger),
            patch('builtins.open', MagicMock()) as mock_file,
        ):

            result = process_chat_message("I just won the lottery!")

            # Verify audio was generated and saved
            assert result["response_audio"] == b"excited_audio_data"
            mock_file.assert_called_once()

    @patch('src.miramind.llm.langgraph.chatbot.initialize_clients')
    @patch('src.miramind.llm.langgraph.subgraphs.generate_response')
    @patch('src.miramind.llm.langgraph.chatbot.call_openai')
    def test_multiple_emotion_routing(
        self, mock_call_openai, mock_generate_response, mock_init_clients
    ):
        """Test that different emotions route to different flows."""
        # Setup mocks
        mock_client = Mock()
        mock_tts_provider = Mock()
        mock_emotion_logger = Mock()
        mock_init_clients.return_value = (mock_client, mock_tts_provider, mock_emotion_logger)

        def mock_response_func(state):
            emotion = state.get("emotion", "neutral")
            response_map = {
                "sad": "I'm sorry to hear that.",
                "happy": "That's wonderful!",
                "angry": "I understand you're upset.",
                "neutral": "I'm here to help.",
            }
            return {
                **state,
                "response": response_map.get(emotion, "I'm here to help."),
                "response_audio": b"audio_data",
                "chat_history": [],
            }

        mock_generate_response.return_value = mock_response_func

        # Test different emotions
        emotions = ["sad", "happy", "angry", "neutral"]

        for emotion in emotions:
            mock_call_openai.return_value = f'{{"emotion": "{emotion}", "confidence": 0.8}}'

            with (
                patch('src.miramind.llm.langgraph.chatbot.client', mock_client),
                patch('src.miramind.llm.langgraph.chatbot.tts_provider', mock_tts_provider),
                patch('src.miramind.llm.langgraph.chatbot.emotion_logger', mock_emotion_logger),
                patch('builtins.open', MagicMock()),
            ):

                result = process_chat_message(f"I'm feeling {emotion}")

                # Verify appropriate response for each emotion
                if emotion == "sad":
                    assert "sorry" in result["response"].lower()
                elif emotion == "happy":
                    assert "wonderful" in result["response"].lower()
                elif emotion == "angry":
                    assert "understand" in result["response"].lower()
                else:  # neutral
                    assert "help" in result["response"].lower()

    def test_memory_usage_tracking(self):
        """Test that memory usage is tracked during processing."""
        perf_monitor = get_performance_monitor()
        perf_monitor.clear_stats()

        # Simulate some operations
        with perf_monitor.track_operation("test_memory_op"):
            # Simulate some work
            data = [i for i in range(1000)]
            del data

        stats = perf_monitor.get_stats("test_memory_op")

        # Should have memory tracking
        assert "count" in stats
        assert stats["count"] == 1
