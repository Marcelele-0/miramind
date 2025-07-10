"""
Pytest configuration for API tests.

This module provides shared fixtures and configuration for testing the FastAPI application.
"""

import os
import sys
import tempfile
from unittest.mock import Mock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables and paths."""
    # Mock environment variables
    test_env = {
        "OPENAI_API_KEY": "test-key-123",
        "AZURE_SPEECH_KEY": "test-azure-key",
        "AZURE_SPEECH_REGION": "test-region",
    }

    with patch.dict(os.environ, test_env):
        yield


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def mock_file_system(temp_dir):
    """Mock file system paths for testing."""
    with (
        patch("miramind.api.const.FRONTEND_PUBLIC_PATH", temp_dir),
        patch("miramind.api.const.NEXTJS_STATIC_PATH", temp_dir),
    ):
        yield temp_dir


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture(autouse=True)
def mock_global_state():
    """Reset global state before each test."""
    from miramind.api.main import api_response_cache, voice_recordings

    # Clear caches
    api_response_cache.clear()
    voice_recordings.clear()

    yield

    # Clean up after test
    api_response_cache.clear()
    voice_recordings.clear()


@pytest.fixture
def mock_audio_file(temp_dir):
    """Create a mock audio file for testing."""
    audio_path = os.path.join(temp_dir, "output.wav")
    with open(audio_path, "wb") as f:
        f.write(b"fake audio data")
    return audio_path


@pytest.fixture
def mock_sessions_file(temp_dir):
    """Create a mock sessions log file for testing."""
    sessions_path = os.path.join(temp_dir, "sessions_log.json")
    import json

    sample_sessions = [
        {
            "sessionId": "test-session-1",
            "startTime": "2025-01-09T14:00:00Z",
            "messages": [
                {
                    "timestamp": "2025-01-09T14:01:00Z",
                    "userInput": "Hello",
                    "emotion": "happy",
                    "confidence": 0.8,
                    "botResponse": "Hi there!",
                }
            ],
        }
    ]

    with open(sessions_path, "w") as f:
        json.dump(sample_sessions, f)

    return sessions_path


@pytest.fixture
def mock_base64_audio():
    """Generate mock base64 encoded audio data."""
    import base64

    fake_audio = b"fake audio data for testing"
    return base64.b64encode(fake_audio).decode()


@pytest.fixture
def disable_background_tasks():
    """Disable background tasks for testing."""
    with patch("fastapi.BackgroundTasks.add_task"):
        yield


@pytest.fixture
def mock_subprocess():
    """Mock subprocess calls for testing."""
    from unittest.mock import AsyncMock

    mock_proc = AsyncMock()
    mock_proc.returncode = 0
    mock_proc.communicate.return_value = (
        b'{"response_text": "Test response", "memory": "test"}',
        b'',
    )

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        yield mock_proc
