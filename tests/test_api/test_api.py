"""
Pytest tests for the MiraMind FastAPI application.

This module contains comprehensive tests for all API endpoints including:
- Chat functionality
- Voice recording and transcription
- Session management
- Audio file serving
- Debug endpoints
"""

import json
import os
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app
from miramind.api.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value = MagicMock(text="Test transcription")
    return mock_client


@pytest.fixture
def sample_chat_input():
    """Sample chat input data for testing."""
    return {
        "userInput": "Hello, how are you?",
        "chatHistory": [
            {"type": "user", "content": "Hi"},
            {"type": "assistant", "content": "Hello! How can I help you today?"},
        ],
        "memory": "User prefers friendly conversation",
        "sessionId": "test-session-123",
    }


@pytest.fixture
def sample_voice_input():
    """Sample voice recording input data for testing."""
    return {"duration": 10, "chunk_duration": 5, "lag": 2, "sessionId": "test-voice-session-456"}


@pytest.fixture
def sample_sessions_data():
    """Sample sessions data for testing."""
    return [
        {
            "sessionId": "test-session-123",
            "startTime": "2025-01-09T14:00:00Z",
            "messages": [
                {
                    "timestamp": "2025-01-09T14:01:00Z",
                    "userInput": "Hello",
                    "emotion": "happy",
                    "confidence": 0.8,
                    "botResponse": "Hi there! How can I help you today?",
                }
            ],
        }
    ]


class TestHealthEndpoints:
    """Test health and utility endpoints."""

    def test_test_endpoint(self, client):
        """Test the basic test endpoint."""
        response = client.get("/api/test")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "API is working"
        assert "timestamp" in data


class TestChatEndpoints:
    """Test chat-related endpoints."""

    def test_start_call(self, client):
        """Test starting a new call session."""
        with (
            patch("os.path.exists", return_value=False),
            patch("builtins.open", mock_open()),
            patch("json.dump"),
        ):

            response = client.post("/api/chat/start")
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Call started"
            assert "sessionId" in data
            assert len(data["sessionId"]) == 36  # UUID length

    @patch("miramind.api.main.process_chat_message_async")
    def test_chat_message_success(self, mock_process_chat, client, sample_chat_input):
        """Test successful chat message processing."""
        # Mock the async chat processing
        mock_process_chat.return_value = {
            "response_text": "Hello! I'm doing well, thank you for asking.",
            "audio_file_path": "/path/to/audio.wav",
            "memory": "User is friendly and polite",
        }

        response = client.post("/api/chat/message", json=sample_chat_input)
        assert response.status_code == 200
        data = response.json()
        assert "response_text" in data
        assert "audio_file_path" in data
        assert "memory" in data
        assert "processing_time" in data
        mock_process_chat.assert_called_once()

    @patch("miramind.api.main.process_chat_message_async")
    def test_chat_message_cache_hit(self, mock_process_chat, client, sample_chat_input):
        """Test chat message with cache hit."""
        # First call to populate cache
        mock_process_chat.return_value = {
            "response_text": "Cached response",
            "audio_file_path": None,
            "memory": "test memory",
        }

        # Make first request
        response1 = client.post("/api/chat/message", json=sample_chat_input)
        assert response1.status_code == 200

        # Make second request with same input - should hit cache
        response2 = client.post("/api/chat/message", json=sample_chat_input)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2.get("cached") is True

        # Should only call the async function once (for first request)
        assert mock_process_chat.call_count == 1

    @patch("miramind.api.main.process_chat_message_async")
    def test_chat_message_error_handling(self, mock_process_chat, client, sample_chat_input):
        """Test chat message error handling with fallback."""
        # Mock the async function to raise an exception
        mock_process_chat.side_effect = Exception("Async processing failed")

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            # Mock successful subprocess fallback
            mock_proc = AsyncMock()
            mock_proc.returncode = 0
            mock_proc.communicate.return_value = (
                b'Some output\n{"response_text": "Fallback response", "memory": "fallback"}',
                b'',
            )
            mock_subprocess.return_value = mock_proc

            response = client.post("/api/chat/message", json=sample_chat_input)
            assert response.status_code == 200
            data = response.json()
            assert data["response_text"] == "Fallback response"


class TestTranscriptEndpoints:
    """Test transcript and session-related endpoints."""

    def test_get_transcripts_no_file(self, client):
        """Test getting transcripts when no session file exists."""
        with patch("os.path.exists", return_value=False):
            response = client.get("/api/transcripts")
            assert response.status_code == 200
            data = response.json()
            assert data["transcripts"] == []

    def test_get_transcripts_with_data(self, client, sample_sessions_data):
        """Test getting transcripts with existing session data."""
        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=json.dumps(sample_sessions_data))),
        ):

            response = client.get("/api/transcripts")
            assert response.status_code == 200
            data = response.json()
            assert "transcripts" in data
            assert len(data["transcripts"]) == 1
            transcript = data["transcripts"][0]
            assert transcript["id"] == "test-session-123"
            assert "conversation" in transcript
            assert "primaryEmotion" in transcript
            assert "averageConfidence" in transcript


class TestAudioEndpoints:
    """Test audio file serving endpoints."""

    def test_get_audio_file_exists(self, client):
        """Test getting audio file when it exists."""
        with (
            patch("os.path.exists", return_value=True),
            patch("miramind.api.main.FRONTEND_PUBLIC_PATH", "/mock/path"),
        ):

            response = client.get("/api/audio/output.wav")
            assert response.status_code == 200

    def test_get_audio_file_not_exists(self, client):
        """Test getting audio file when it doesn't exist."""
        with patch("os.path.exists", return_value=False):
            response = client.get("/api/audio/output.wav")
            assert response.status_code == 404
            data = response.json()
            assert data["error"] == "Audio file not found"

    def test_get_audio_file_simple_endpoint(self, client):
        """Test the simple audio file endpoint."""
        with patch("os.path.exists", return_value=False):
            response = client.get("/output.wav")
            assert response.status_code == 404


class TestVoiceEndpoints:
    """Test voice recording and processing endpoints."""

    def test_upload_voice_no_openai_client(self, client):
        """Test voice upload when OpenAI client is not initialized."""
        with patch("miramind.api.main.openai_client", None):
            response = client.post(
                "/api/voice/upload", files={"file": ("test.wav", b"fake audio data", "audio/wav")}
            )
            assert response.status_code == 500
            assert "OpenAI client not initialized" in response.json()["detail"]

    def test_upload_voice_invalid_file_type(self, client):
        """Test voice upload with invalid file type."""
        with patch("miramind.api.main.openai_client", MagicMock()):
            response = client.post(
                "/api/voice/upload", files={"file": ("test.txt", b"not audio", "text/plain")}
            )
            assert response.status_code == 400
            assert "File must be an audio file" in response.json()["detail"]

    @patch("miramind.api.main.openai_client")
    @patch("miramind.api.main.STT")
    def test_upload_voice_success(self, mock_stt_class, mock_openai_client, client):
        """Test successful voice upload and transcription."""
        # Mock STT instance
        mock_stt = MagicMock()
        mock_stt.transcribe_bytes.return_value = {"transcript": "Hello, this is a test"}
        mock_stt_class.return_value = mock_stt

        response = client.post(
            "/api/voice/upload", files={"file": ("test.wav", b"fake audio data", "audio/wav")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["transcript"] == "Hello, this is a test"
        assert data["success"] is True

    def test_start_voice_recording_no_openai(self, client, sample_voice_input):
        """Test starting voice recording without OpenAI client."""
        with patch("miramind.api.main.openai_client", None):
            response = client.post("/api/voice/start-recording", json=sample_voice_input)
            assert response.status_code == 500

    @patch("miramind.api.main.openai_client")
    def test_start_voice_recording_success(self, mock_openai_client, client, sample_voice_input):
        """Test successful voice recording start."""
        response = client.post("/api/voice/start-recording", json=sample_voice_input)
        assert response.status_code == 200
        data = response.json()
        assert "recording_id" in data
        assert data["status"] == "recording"
        assert data["duration"] == 10

    def test_stop_voice_recording_not_found(self, client):
        """Test stopping a non-existent voice recording."""
        response = client.post("/api/voice/stop-recording/nonexistent-id")
        assert response.status_code == 404
        assert "Recording session not found" in response.json()["detail"]

    @patch("miramind.api.main.voice_recordings")
    def test_stop_voice_recording_success(self, mock_recordings, client):
        """Test successful voice recording stop."""
        # Setup existing recording
        recording_id = "test-recording-123"
        mock_recordings.__contains__ = lambda self, key: key == recording_id
        mock_recordings.__getitem__ = lambda self, key: {
            "status": "recording",
            "duration": 10,
            "transcripts": ["Hello", "World"],
        }
        mock_recordings.__setitem__ = lambda self, key, value: None

        response = client.post(f"/api/voice/stop-recording/{recording_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["recording_id"] == recording_id
        assert data["status"] == "stopped"

    @patch("miramind.api.main.openai_client")
    @patch("miramind.api.main.timed_listen_and_transcribe")
    def test_record_and_transcribe_success(
        self, mock_listen, mock_openai_client, client, sample_voice_input
    ):
        """Test successful record and transcribe."""
        from queue import Queue

        # Mock the transcript buffer
        mock_buffer = Queue()
        mock_buffer.put({"transcript": "Hello"})
        mock_buffer.put({"transcript": "World"})
        mock_listen.return_value = mock_buffer

        response = client.post("/api/voice/record-and-transcribe", json=sample_voice_input)
        assert response.status_code == 200
        data = response.json()
        assert "transcript" in data
        assert data["success"] is True

    @patch("miramind.api.main.openai_client")
    @patch("miramind.api.main.process_chat_message_async")
    @patch("miramind.api.main.STT")
    def test_voice_chat_success(
        self, mock_stt_class, mock_process_chat, mock_openai_client, client
    ):
        """Test successful voice chat processing."""
        # Mock STT
        mock_stt = MagicMock()
        mock_stt.transcribe_bytes.return_value = {"transcript": "Hello assistant"}
        mock_stt_class.return_value = mock_stt

        # Mock chat processing
        mock_process_chat.return_value = {
            "response_text": "Hello! How can I help you?",
            "audio_file_path": "/path/to/response.wav",
            "memory": "User said hello",
        }

        # Sample base64 audio data
        import base64

        audio_data = base64.b64encode(b"fake audio data").decode()

        voice_chat_input = {
            "audioData": audio_data,
            "chatHistory": [],
            "memory": "",
            "sessionId": "voice-chat-session",
        }

        response = client.post("/api/voice/chat", json=voice_chat_input)
        assert response.status_code == 200
        data = response.json()
        assert data["transcript"] == "Hello assistant"
        assert "response_text" in data
        assert "processing_time" in data


class TestDebugEndpoints:
    """Test debug and utility endpoints."""

    def test_debug_files_endpoint(self, client):
        """Test the debug files endpoint."""
        with (
            patch("os.path.exists", return_value=True),
            patch("os.listdir", return_value=["output.wav", "test.mp3"]),
            patch("os.stat") as mock_stat,
        ):

            mock_stat.return_value = MagicMock(st_size=1024, st_mtime=1234567890)

            response = client.get("/api/debug/files")
            assert response.status_code == 200
            data = response.json()
            assert "frontend_public_path" in data
            assert "frontend_public_exists" in data
            assert "files_in_public" in data
            assert "output_wav_info" in data


class TestBackgroundTasks:
    """Test background task functionality."""

    @patch("builtins.open", mock_open(read_data='[]'))
    @patch("json.dump")
    def test_save_message_to_session_async(self, mock_json_dump):
        """Test async session message saving."""
        # This would normally be called as a background task
        # We can test the synchronous helper function
        from miramind.api.main import _save_session_sync, save_message_to_session_async

        with patch("builtins.open", mock_open(read_data='[{"sessionId": "test", "messages": []}]')):
            _save_session_sync(
                sessions_log_path="/fake/path",
                session_id="test",
                user_input="Hello",
                bot_response="Hi there",
                emotion="happy",
                confidence=0.8,
            )
            mock_json_dump.assert_called_once()


class TestCacheManagement:
    """Test API cache functionality."""

    def test_cache_key_generation(self):
        """Test cache key generation."""
        from miramind.api.main import _get_cache_key

        key1 = _get_cache_key("Hello", 5)
        key2 = _get_cache_key("hello", 5)  # Should be same (case insensitive)
        key3 = _get_cache_key("Hello", 6)  # Should be different (different history length)

        assert key1 == key2
        assert key1 != key3

    def test_cache_validity(self):
        """Test cache validity checking."""
        import time

        from miramind.api.main import _is_cache_valid

        current_time = time.time()
        assert _is_cache_valid(current_time) is True
        assert _is_cache_valid(current_time - 400) is False  # Older than TTL

    def test_cache_cleanup(self):
        """Test cache cleanup functionality."""
        import time

        from miramind.api.main import _cleanup_api_cache, api_response_cache

        # Add some test entries
        api_response_cache.clear()
        current_time = time.time()
        api_response_cache["valid"] = ({"data": "valid"}, current_time)
        api_response_cache["expired"] = ({"data": "expired"}, current_time - 400)

        _cleanup_api_cache()

        assert "valid" in api_response_cache
        assert "expired" not in api_response_cache


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_chat_message_with_invalid_input(self, client):
        """Test chat message with invalid input format."""
        response = client.post("/api/chat/message", json={"invalid": "data"})
        assert response.status_code == 422  # Validation error

    def test_voice_chat_without_audio_data(self, client):
        """Test voice chat without audio data."""
        with patch("miramind.api.main.openai_client", MagicMock()):
            voice_chat_input = {"chatHistory": [], "memory": "", "sessionId": "test"}

            response = client.post("/api/voice/chat", json=voice_chat_input)
            assert response.status_code == 400
            assert "No transcript available" in response.json()["detail"]


@pytest.mark.asyncio
class TestAsyncFunctionality:
    """Test async functionality where needed."""

    async def test_cleanup_old_recordings(self):
        """Test cleanup of old recording sessions."""
        from datetime import datetime, timedelta

        from miramind.api.main import cleanup_old_recordings, voice_recordings

        # Setup test data
        voice_recordings.clear()
        old_time = (datetime.now() - timedelta(hours=2)).isoformat()
        new_time = datetime.now().isoformat()

        voice_recordings["old_session"] = {"start_time": old_time}
        voice_recordings["new_session"] = {"start_time": new_time}

        await cleanup_old_recordings()

        assert "old_session" not in voice_recordings
        assert "new_session" in voice_recordings


if __name__ == "__main__":
    pytest.main([__file__])
