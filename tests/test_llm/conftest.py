import os
import sys
from unittest.mock import Mock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    client = Mock()
    client.chat.completions.create.return_value = Mock()
    client.chat.completions.create.return_value.choices = [Mock()]
    client.chat.completions.create.return_value.choices[0].message.content = "Test response"
    return client


@pytest.fixture
def mock_tts_provider():
    """Mock TTS provider for testing."""
    provider = Mock()
    provider.synthesize.return_value = b"test_audio_data"
    provider.set_emotion = Mock()
    return provider


@pytest.fixture
def mock_emotion_logger():
    """Mock emotion logger for testing."""
    logger = Mock()
    return logger


@pytest.fixture
def sample_chat_state():
    """Sample chat state for testing."""
    return {
        "user_input": "Hello, how are you?",
        "emotion": "neutral",
        "emotion_confidence": 0.7,
        "chat_history": [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello there!"},
        ],
        "memory": "",
    }


@pytest.fixture
def sample_emotion_states():
    """Sample emotion states for testing different emotions."""
    return {
        "happy": {
            "user_input": "I'm so happy today!",
            "emotion": "happy",
            "emotion_confidence": 0.9,
            "chat_history": [],
        },
        "sad": {
            "user_input": "I'm feeling really sad.",
            "emotion": "sad",
            "emotion_confidence": 0.85,
            "chat_history": [],
        },
        "angry": {
            "user_input": "I'm so frustrated!",
            "emotion": "angry",
            "emotion_confidence": 0.8,
            "chat_history": [],
        },
        "neutral": {
            "user_input": "Just a regular day.",
            "emotion": "neutral",
            "emotion_confidence": 0.6,
            "chat_history": [],
        },
    }


@pytest.fixture
def mock_environment_vars():
    """Mock environment variables for testing."""
    env_vars = {
        "OPENAI_API_KEY": "test_openai_key",
        "AZURE_SPEECH_KEY": "test_azure_key",
        "AZURE_SPEECH_ENDPOINT": "https://test.cognitive.microsoft.com/",
        "AZURE_SPEECH_VOICE_NAME": "en-US-AriaNeural",
    }
    return env_vars


@pytest.fixture(autouse=True)
def setup_test_environment(mock_environment_vars):
    """Setup test environment with mocked environment variables."""
    with patch.dict(os.environ, mock_environment_vars):
        yield


@pytest.fixture
def temp_log_file(tmp_path):
    """Create a temporary log file for testing."""
    log_file = tmp_path / "test_emotion_log.json"
    return str(log_file)


@pytest.fixture
def sample_log_entries():
    """Sample log entries for testing."""
    return [
        {
            "input": "I'm happy!",
            "emotion": "happy",
            "confidence": 0.9,
            "response": "That's wonderful to hear!",
        },
        {
            "input": "I'm sad.",
            "emotion": "sad",
            "confidence": 0.85,
            "response": "I'm sorry to hear that.",
        },
    ]


@pytest.fixture
def mock_performance_monitor():
    """Mock performance monitor for testing."""
    monitor = Mock()
    monitor.track_operation.return_value.__enter__ = Mock()
    monitor.track_operation.return_value.__exit__ = Mock()
    monitor.get_stats.return_value = {}
    monitor.clear_stats.return_value = None
    return monitor


@pytest.fixture
def mock_graph_components():
    """Mock graph components for testing."""
    return {
        "client": Mock(),
        "tts_provider": Mock(),
        "emotion_logger": Mock(),
        "compiled_graph": Mock(),
    }


# Configure pytest to handle async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test markers for different test categories
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running tests")


# Pytest collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test items during collection."""
    for item in items:
        # Add markers based on test names
        if "integration" in item.name.lower():
            item.add_marker(pytest.mark.integration)
        elif "performance" in item.name.lower():
            item.add_marker(pytest.mark.performance)
        else:
            item.add_marker(pytest.mark.unit)

        # Mark slow tests
        if "slow" in item.name.lower() or "end_to_end" in item.name.lower():
            item.add_marker(pytest.mark.slow)


# Skip tests based on conditions
def pytest_runtest_setup(item):
    """Setup before running each test."""
    # Skip integration tests if not requested
    if "integration" in item.keywords and not item.config.getoption(
        "--run-integration", default=False
    ):
        pytest.skip("Integration tests not requested")

    # Skip slow tests if not requested
    if "slow" in item.keywords and not item.config.getoption("--run-slow", default=False):
        pytest.skip("Slow tests not requested")


def pytest_addoption(parser):
    """Add command line options to pytest."""
    parser.addoption(
        "--run-integration", action="store_true", default=False, help="Run integration tests"
    )
    parser.addoption("--run-slow", action="store_true", default=False, help="Run slow tests")
    parser.addoption(
        "--run-performance", action="store_true", default=False, help="Run performance tests"
    )


# Cleanup after tests
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test."""
    yield
    # Clear any global state
    from src.miramind.llm.langgraph.run_chat import response_cache

    response_cache.clear()

    # Clear performance monitor
    from src.miramind.llm.langgraph.performance_monitor import get_performance_monitor

    get_performance_monitor().clear_stats()
