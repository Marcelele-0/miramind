import json
import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.miramind.llm.langgraph.chatbot import (
    DEFAULT_MODEL,
    EMOTION_PROMPT,
    RESPONSE_MODEL,
    VALID_EMOTIONS,
    EmotionResult,
    detect_emotion,
    get_chatbot,
    get_graph,
    initialize_clients,
)


class TestChatbot:
    """Test suite for the chatbot module."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_client = Mock()
        self.mock_tts_provider = Mock()
        self.mock_emotion_logger = Mock()

        # Mock state for testing
        self.test_state = {"user_input": "I am feeling sad today", "chat_history": [], "memory": ""}

    def test_emotion_result_model_validation(self):
        """Test EmotionResult pydantic model validation."""
        # Valid emotion result
        result = EmotionResult(emotion="happy", confidence=0.85)
        assert result.emotion == "happy"
        assert result.confidence == 0.85

        # Test with valid emotions
        for emotion in VALID_EMOTIONS:
            result = EmotionResult(emotion=emotion, confidence=0.5)
            assert result.emotion == emotion

    def test_emotion_result_model_invalid_confidence(self):
        """Test EmotionResult with invalid confidence values."""
        # Should still work with out-of-range confidence
        result = EmotionResult(emotion="happy", confidence=1.5)
        assert result.confidence == 1.5

    @patch('src.miramind.llm.langgraph.chatbot.call_openai')
    def test_detect_emotion_valid_response(self, mock_call_openai):
        """Test emotion detection with valid JSON response."""
        mock_call_openai.return_value = '{"emotion": "sad", "confidence": 0.92}'

        result = detect_emotion(self.test_state)

        assert result["emotion"] == "sad"
        assert result["emotion_confidence"] == 0.92
        assert result["user_input"] == "I am feeling sad today"
        assert len(result["chat_history"]) == 1
        assert result["chat_history"][0]["role"] == "user"
        assert result["chat_history"][0]["content"] == "I am feeling sad today"

    @patch('src.miramind.llm.langgraph.chatbot.call_openai')
    def test_detect_emotion_invalid_json(self, mock_call_openai):
        """Test emotion detection with invalid JSON response."""
        mock_call_openai.return_value = "This is not valid JSON"

        result = detect_emotion(self.test_state)

        # Should default to neutral
        assert result["emotion"] == "neutral"
        assert result["emotion_confidence"] == 0.0

    @patch('src.miramind.llm.langgraph.chatbot.call_openai')
    def test_detect_emotion_invalid_emotion(self, mock_call_openai):
        """Test emotion detection with invalid emotion in response."""
        mock_call_openai.return_value = '{"emotion": "invalid_emotion", "confidence": 0.85}'

        result = detect_emotion(self.test_state)

        # Should default to neutral for invalid emotions
        assert result["emotion"] == "neutral"
        assert result["emotion_confidence"] == 0.0

    @patch('src.miramind.llm.langgraph.chatbot.call_openai')
    def test_detect_emotion_partial_json(self, mock_call_openai):
        """Test emotion detection with partial JSON in response."""
        mock_call_openai.return_value = (
            'Some text before {"emotion": "happy", "confidence": 0.75} some text after'
        )

        result = detect_emotion(self.test_state)

        assert result["emotion"] == "happy"
        assert result["emotion_confidence"] == 0.75

    @patch('src.miramind.llm.langgraph.chatbot.call_openai')
    def test_detect_emotion_api_error(self, mock_call_openai):
        """Test emotion detection when OpenAI API fails."""
        mock_call_openai.side_effect = Exception("API Error")

        result = detect_emotion(self.test_state)

        # Should default to neutral on API error
        assert result["emotion"] == "neutral"
        assert result["emotion_confidence"] == 0.0

    @patch('src.miramind.llm.langgraph.chatbot.initialize_clients')
    @patch('src.miramind.llm.langgraph.subgraphs.build_sad_flow')
    @patch('src.miramind.llm.langgraph.subgraphs.build_angry_flow')
    @patch('src.miramind.llm.langgraph.subgraphs.build_excited_flow')
    @patch('src.miramind.llm.langgraph.subgraphs.build_gentle_flow')
    @patch('src.miramind.llm.langgraph.subgraphs.build_neutral_flow')
    def test_get_graph_structure(
        self, mock_neutral, mock_gentle, mock_excited, mock_angry, mock_sad, mock_init
    ):
        """Test that get_graph creates proper graph structure."""
        # Setup mocks
        mock_init.return_value = (
            self.mock_client,
            self.mock_tts_provider,
            self.mock_emotion_logger,
        )

        # Mock subgraph builders to return mock compiled graphs
        mock_compiled_graph = Mock()
        mock_sad.return_value.compile.return_value = mock_compiled_graph
        mock_angry.return_value.compile.return_value = mock_compiled_graph
        mock_excited.return_value.compile.return_value = mock_compiled_graph
        mock_gentle.return_value.compile.return_value = mock_compiled_graph
        mock_neutral.return_value.compile.return_value = mock_compiled_graph

        # Mock the global variables
        with (
            patch('src.miramind.llm.langgraph.chatbot.client', self.mock_client),
            patch('src.miramind.llm.langgraph.chatbot.tts_provider', self.mock_tts_provider),
            patch('src.miramind.llm.langgraph.chatbot.emotion_logger', self.mock_emotion_logger),
        ):

            graph = get_graph()

            # Verify graph was created
            assert graph is not None

            # Verify subgraph builders were called
            mock_sad.assert_called_once()
            mock_angry.assert_called_once()
            mock_excited.assert_called_once()
            mock_gentle.assert_called_once()
            mock_neutral.assert_called_once()

    @patch('src.miramind.llm.langgraph.chatbot.get_tts_provider')
    @patch('src.miramind.llm.langgraph.chatbot.OpenAI')
    @patch('src.miramind.llm.langgraph.chatbot.EmotionLogger')
    @patch('src.miramind.llm.langgraph.chatbot.load_dotenv')
    def test_initialize_clients(
        self, mock_load_dotenv, mock_emotion_logger, mock_openai, mock_get_tts
    ):
        """Test client initialization."""
        # Setup mocks
        mock_openai_instance = Mock()
        mock_tts_instance = Mock()
        mock_logger_instance = Mock()

        mock_openai.return_value = mock_openai_instance
        mock_get_tts.return_value = mock_tts_instance
        mock_emotion_logger.return_value = mock_logger_instance

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            client, tts, logger = initialize_clients()

            # Verify initialization
            mock_load_dotenv.assert_called_once()
            mock_openai.assert_called_once()
            mock_get_tts.assert_called_once_with("azure")
            mock_emotion_logger.assert_called_once()

            assert client == mock_openai_instance
            assert tts == mock_tts_instance
            assert logger == mock_logger_instance

    @patch('src.miramind.llm.langgraph.chatbot.main')
    def test_get_chatbot_initialization(self, mock_main):
        """Test chatbot initialization and caching."""
        mock_chatbot = Mock()
        mock_main.return_value = mock_chatbot

        # Clear any existing chatbot instance
        with patch('src.miramind.llm.langgraph.chatbot.chatbot', None):
            chatbot1 = get_chatbot()
            chatbot2 = get_chatbot()

            # Should initialize only once
            mock_main.assert_called_once()
            assert chatbot1 == mock_chatbot
            assert chatbot2 == mock_chatbot

    def test_emotion_prompt_contains_required_elements(self):
        """Test that emotion prompt contains all required elements."""
        assert "neurodivergent children" in EMOTION_PROMPT
        assert "JSON format" in EMOTION_PROMPT
        assert "emotion" in EMOTION_PROMPT
        assert "confidence" in EMOTION_PROMPT

        # Check that all valid emotions are mentioned
        for emotion in VALID_EMOTIONS:
            assert emotion in EMOTION_PROMPT

    def test_model_constants(self):
        """Test that model constants are properly set."""
        assert DEFAULT_MODEL == "gpt-4o-mini"
        assert RESPONSE_MODEL == "gpt-4o"
        assert isinstance(VALID_EMOTIONS, set)
        assert len(VALID_EMOTIONS) == 8

    def test_valid_emotions_completeness(self):
        """Test that valid emotions contain expected values."""
        expected_emotions = {
            "happy",
            "sad",
            "angry",
            "scared",
            "excited",
            "embarrassed",
            "anxious",
            "neutral",
        }
        assert VALID_EMOTIONS == expected_emotions

    @patch('src.miramind.llm.langgraph.chatbot.call_openai')
    def test_detect_emotion_preserves_state(self, mock_call_openai):
        """Test that detect_emotion preserves and extends state properly."""
        mock_call_openai.return_value = '{"emotion": "happy", "confidence": 0.8}'

        initial_state = {
            "user_input": "I love this!",
            "chat_history": [{"role": "assistant", "content": "Hello"}],
            "memory": "previous context",
            "custom_field": "should be preserved",
        }

        result = detect_emotion(initial_state)

        # Check that original state is preserved
        assert result["memory"] == "previous context"
        assert result["custom_field"] == "should be preserved"

        # Check that new fields are added
        assert result["emotion"] == "happy"
        assert result["emotion_confidence"] == 0.8

        # Check that chat history is extended
        assert len(result["chat_history"]) == 2
        assert result["chat_history"][0]["role"] == "assistant"
        assert result["chat_history"][1]["role"] == "user"
        assert result["chat_history"][1]["content"] == "I love this!"

    @patch('src.miramind.llm.langgraph.chatbot.call_openai')
    def test_detect_emotion_with_existing_chat_history(self, mock_call_openai):
        """Test emotion detection with existing chat history."""
        mock_call_openai.return_value = '{"emotion": "excited", "confidence": 0.9}'

        state_with_history = {
            "user_input": "This is amazing!",
            "chat_history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
        }

        result = detect_emotion(state_with_history)

        # Should preserve existing history and add new message
        assert len(result["chat_history"]) == 3
        assert result["chat_history"][0]["content"] == "Hello"
        assert result["chat_history"][1]["content"] == "Hi there!"
        assert result["chat_history"][2]["content"] == "This is amazing!"
        assert result["chat_history"][2]["role"] == "user"
