import asyncio
import json
import os
import sys
import threading
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.miramind.llm.langgraph.utils import (
    DEFAULT_MODEL,
    LOG_FILE,
    EmotionLogger,
    call_openai,
    call_openai_async,
    generate_response,
    main,
)


class TestEmotionLogger:
    """Test suite for EmotionLogger class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.log_file = "test_emotion_log.json"
        self.logger = EmotionLogger(self.log_file)

    def teardown_method(self):
        """Clean up test files."""
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

    def test_emotion_logger_initialization(self):
        """Test EmotionLogger initialization."""
        assert self.logger.filepath == self.log_file

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    @patch('json.load')
    @patch('json.dump')
    def test_log_new_file(self, mock_json_dump, mock_json_load, mock_exists, mock_file):
        """Test logging to a new file."""
        mock_exists.return_value = False

        self.logger.log("Hello", "happy", 0.85, "Great to hear!")

        # Should create new file with one entry
        mock_json_dump.assert_called_once()
        args, kwargs = mock_json_dump.call_args
        logged_data = args[0]

        assert len(logged_data) == 1
        assert logged_data[0]["input"] == "Hello"
        assert logged_data[0]["emotion"] == "happy"
        assert logged_data[0]["confidence"] == 0.85
        assert logged_data[0]["response"] == "Great to hear!"

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    @patch('json.load')
    @patch('json.dump')
    def test_log_existing_file(self, mock_json_dump, mock_json_load, mock_exists, mock_file):
        """Test logging to an existing file."""
        mock_exists.return_value = True
        mock_json_load.return_value = [
            {"input": "previous", "emotion": "neutral", "confidence": 0.5, "response": "ok"}
        ]

        self.logger.log("Hello", "sad", 0.75, "I understand")

        # Should append to existing data
        mock_json_dump.assert_called_once()
        args, kwargs = mock_json_dump.call_args
        logged_data = args[0]

        assert len(logged_data) == 2
        assert logged_data[0]["input"] == "previous"
        assert logged_data[1]["input"] == "Hello"
        assert logged_data[1]["emotion"] == "sad"
        assert logged_data[1]["confidence"] == 0.75
        assert logged_data[1]["response"] == "I understand"

    @patch('builtins.open', side_effect=IOError("File write error"))
    @patch('os.path.exists')
    @patch('builtins.print')
    def test_log_file_error(self, mock_print, mock_exists, mock_open):
        """Test logging when file operation fails."""
        mock_exists.return_value = False

        # Should not raise exception, just print error
        self.logger.log("Hello", "happy", 0.85, "Great!")

        mock_print.assert_called_once_with("Logging failed: File write error")

    def test_log_confidence_rounding(self):
        """Test that confidence values are properly rounded."""
        with (
            patch('builtins.open', new_callable=mock_open) as mock_file,
            patch('os.path.exists', return_value=False),
            patch('json.dump') as mock_json_dump,
        ):

            self.logger.log("Hello", "happy", 0.8547, "Great!")

            args, kwargs = mock_json_dump.call_args
            logged_data = args[0]

            assert logged_data[0]["confidence"] == 0.85


class TestCallOpenAI:
    """Test suite for OpenAI API calling functions."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_client = Mock()
        self.test_messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
        ]

    def test_call_openai_success(self):
        """Test successful OpenAI API call."""
        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "  Hello there!  "

        self.mock_client.chat.completions.create.return_value = mock_response

        result = call_openai(self.mock_client, self.test_messages)

        assert result == "Hello there!"
        self.mock_client.chat.completions.create.assert_called_once_with(
            model=DEFAULT_MODEL,
            messages=self.test_messages,
            max_tokens=None,
            temperature=0.7,
            stream=False,
            timeout=10.0,
        )

    def test_call_openai_with_custom_params(self):
        """Test OpenAI API call with custom parameters."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Custom response"

        self.mock_client.chat.completions.create.return_value = mock_response

        result = call_openai(
            self.mock_client, self.test_messages, model="gpt-4o", max_tokens=100, temperature=0.5
        )

        assert result == "Custom response"
        self.mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4o",
            messages=self.test_messages,
            max_tokens=100,
            temperature=0.5,
            stream=False,
            timeout=10.0,
        )

    def test_call_openai_api_error(self):
        """Test OpenAI API call with error."""
        self.mock_client.chat.completions.create.side_effect = Exception("API Error")

        result = call_openai(self.mock_client, self.test_messages)

        assert result == ""

    @pytest.mark.asyncio
    async def test_call_openai_async_success(self):
        """Test successful async OpenAI API call."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Async response"

        self.mock_client.chat.completions.create.return_value = mock_response

        result = await call_openai_async(self.mock_client, self.test_messages)

        assert result == "Async response"

    @pytest.mark.asyncio
    async def test_call_openai_async_error(self):
        """Test async OpenAI API call with error."""
        self.mock_client.chat.completions.create.side_effect = Exception("Async API Error")

        result = await call_openai_async(self.mock_client, self.test_messages)

        assert result == ""


class TestGenerateResponse:
    """Test suite for generate_response function."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_client = Mock()
        self.mock_tts_provider = Mock()
        self.mock_emotion_logger = Mock()

        self.test_state = {
            "user_input": "I am feeling sad",
            "emotion": "sad",
            "emotion_confidence": 0.85,
            "chat_history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
        }

    @patch('src.miramind.llm.langgraph.utils.call_openai')
    def test_generate_response_basic(self, mock_call_openai):
        """Test basic response generation."""
        mock_call_openai.return_value = "I understand you're feeling sad."
        self.mock_tts_provider.synthesize.return_value = b"audio_data"

        responder = generate_response(
            "supportive", self.mock_client, self.mock_tts_provider, self.mock_emotion_logger
        )
        result = responder(self.test_state)

        assert result["response"] == "I understand you're feeling sad."
        assert result["response_audio"] == b"audio_data"
        assert len(result["chat_history"]) == 4  # Original 2 + user input + assistant response

    @patch('src.miramind.llm.langgraph.utils.call_openai')
    def test_generate_response_system_message(self, mock_call_openai):
        """Test that system message is properly formatted."""
        mock_call_openai.return_value = "Test response"
        self.mock_tts_provider.synthesize.return_value = b"audio_data"

        responder = generate_response(
            "gentle", self.mock_client, self.mock_tts_provider, self.mock_emotion_logger
        )
        responder(self.test_state)

        # Check that call_openai was called with correct system message
        mock_call_openai.assert_called_once()
        messages = mock_call_openai.call_args[0][1]

        system_message = messages[0]
        assert system_message["role"] == "system"
        assert "gentle non-licensed therapist" in system_message["content"]
        assert "neurodivergent children" in system_message["content"]

    @patch('src.miramind.llm.langgraph.utils.call_openai')
    def test_generate_response_chat_history_limit(self, mock_call_openai):
        """Test that chat history is limited to last 4 messages."""
        mock_call_openai.return_value = "Response"
        self.mock_tts_provider.synthesize.return_value = b"audio_data"

        # Create state with long chat history
        long_history = [{"role": "user", "content": f"Message {i}"} for i in range(10)]
        state_with_long_history = {**self.test_state, "chat_history": long_history}

        responder = generate_response(
            "neutral", self.mock_client, self.mock_tts_provider, self.mock_emotion_logger
        )
        responder(state_with_long_history)

        # Check that only last 4 messages + system + current user message are used
        mock_call_openai.assert_called_once()
        messages = mock_call_openai.call_args[0][1]

        # Should be: system + last 4 from history + current user input = 6 total
        assert len(messages) == 6

    @patch('src.miramind.llm.langgraph.utils.call_openai')
    def test_generate_response_emotion_mapping(self, mock_call_openai):
        """Test emotion mapping for TTS."""
        mock_call_openai.return_value = "Response"
        self.mock_tts_provider.synthesize.return_value = b"audio_data"

        # Test different emotions
        test_cases = [
            ("anxious", "scared"),
            ("embarrassed", "neutral"),
            ("excited", "excited"),
            ("happy", "happy"),
            ("sad", "sad"),
            ("angry", "angry"),
            ("scared", "scared"),
            ("neutral", "neutral"),
        ]

        for input_emotion, expected_tts_emotion in test_cases:
            state = {**self.test_state, "emotion": input_emotion}
            responder = generate_response(
                "neutral", self.mock_client, self.mock_tts_provider, self.mock_emotion_logger
            )
            responder(state)

            # Check TTS was called with correct emotion
            self.mock_tts_provider.synthesize.assert_called()
            tts_call_args = self.mock_tts_provider.synthesize.call_args[0][0]
            tts_data = json.loads(tts_call_args)
            assert tts_data["emotion"] == expected_tts_emotion

    @patch('src.miramind.llm.langgraph.utils.call_openai')
    def test_generate_response_async_tts(self, mock_call_openai):
        """Test async TTS when available."""
        mock_call_openai.return_value = "Response"
        self.mock_tts_provider.synthesize_async = Mock(return_value=asyncio.Future())
        self.mock_tts_provider.synthesize_async.return_value.set_result(b"async_audio_data")

        responder = generate_response(
            "neutral", self.mock_client, self.mock_tts_provider, self.mock_emotion_logger
        )
        result = responder(self.test_state)

        assert result["response_audio"] == b"async_audio_data"

    @patch('src.miramind.llm.langgraph.utils.call_openai')
    def test_generate_response_tts_error(self, mock_call_openai):
        """Test TTS error handling."""
        mock_call_openai.return_value = "Response"
        self.mock_tts_provider.synthesize.side_effect = Exception("TTS Error")

        responder = generate_response(
            "neutral", self.mock_client, self.mock_tts_provider, self.mock_emotion_logger
        )
        result = responder(self.test_state)

        assert result["response"] == "Response"
        assert result["response_audio"] is None

    @patch('src.miramind.llm.langgraph.utils.call_openai')
    @patch('threading.Thread')
    def test_generate_response_async_logging(self, mock_thread, mock_call_openai):
        """Test async logging functionality."""
        mock_call_openai.return_value = "Response"
        self.mock_tts_provider.synthesize.return_value = b"audio_data"

        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        responder = generate_response(
            "neutral", self.mock_client, self.mock_tts_provider, self.mock_emotion_logger
        )
        responder(self.test_state)

        # Check that logging thread was created and started
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

    @patch('src.miramind.llm.langgraph.utils.call_openai')
    def test_generate_response_preserves_state(self, mock_call_openai):
        """Test that response generation preserves original state."""
        mock_call_openai.return_value = "Response"
        self.mock_tts_provider.synthesize.return_value = b"audio_data"

        original_state = {
            **self.test_state,
            "custom_field": "should be preserved",
            "memory": "important context",
        }

        responder = generate_response(
            "neutral", self.mock_client, self.mock_tts_provider, self.mock_emotion_logger
        )
        result = responder(original_state)

        # Check that original fields are preserved
        assert result["custom_field"] == "should be preserved"
        assert result["memory"] == "important context"
        assert result["user_input"] == "I am feeling sad"
        assert result["emotion"] == "sad"


class TestMain:
    """Test suite for main initialization function."""

    @patch('src.miramind.llm.langgraph.utils.get_tts_provider')
    @patch('src.miramind.llm.langgraph.utils.OpenAI')
    @patch('src.miramind.llm.langgraph.utils.EmotionLogger')
    def test_main_initialization(self, mock_emotion_logger, mock_openai, mock_get_tts):
        """Test main function initialization."""
        mock_client = Mock()
        mock_tts = Mock()
        mock_logger = Mock()

        mock_openai.return_value = mock_client
        mock_get_tts.return_value = mock_tts
        mock_emotion_logger.return_value = mock_logger

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            client, tts_provider, emotion_logger = main()

            assert client == mock_client
            assert tts_provider == mock_tts
            assert emotion_logger == mock_logger

            mock_openai.assert_called_once_with(api_key='test_key')
            mock_get_tts.assert_called_once_with("azure")
            mock_emotion_logger.assert_called_once_with(LOG_FILE)

    def test_constants(self):
        """Test module constants."""
        assert DEFAULT_MODEL == "gpt-4o"
        assert LOG_FILE == "emotion_log.json"
