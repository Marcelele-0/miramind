import os
import sys

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from src.miramind.audio.tts.tts_azure import AzureTTSProvider
from src.miramind.audio.tts.tts_base import TTSProvider
from src.miramind.audio.tts.tts_factory import get_tts_provider


class TestTTSFactorySimple:
    """Simple tests for TTS Factory functionality."""

    def test_factory_creates_azure_provider(self):
        """Test that factory creates Azure provider correctly."""
        with pytest.MonkeyPatch().context() as mp:
            mp.setenv("AZURE_SPEECH_ENDPOINT", "https://test.api.cognitive.microsoft.com/")
            mp.setenv("AZURE_SPEECH_KEY", "test_key")

            provider = get_tts_provider("azure")

            assert provider is not None
            assert hasattr(provider, 'synthesize')
            assert hasattr(provider, 'set_emotion')
            assert provider.endpoint == "https://test.api.cognitive.microsoft.com/"
            assert provider.subscription_key == "test_key"

    def test_factory_uses_default_provider(self):
        """Test that factory defaults to azure provider."""
        with pytest.MonkeyPatch().context() as mp:
            mp.setenv("AZURE_SPEECH_ENDPOINT", "https://test.api.cognitive.microsoft.com/")
            mp.setenv("AZURE_SPEECH_KEY", "test_key")

            provider = get_tts_provider()  # No provider name specified

            assert provider is not None
            assert hasattr(provider, 'synthesize')

    def test_factory_rejects_unknown_provider(self):
        """Test that factory raises error for unknown provider."""
        with pytest.raises(ValueError, match="Unknown TTS provider"):
            get_tts_provider("unknown_provider")

    def test_factory_uses_environment_variables(self):
        """Test that factory reads from environment variables."""
        test_endpoint = "https://custom.endpoint.com/"
        test_key = "custom_key_123"
        test_voice = "en-US-AriaNeural"
        with pytest.MonkeyPatch().context() as mp:
            mp.setenv("AZURE_SPEECH_ENDPOINT", test_endpoint)
            mp.setenv("AZURE_SPEECH_KEY", test_key)
            mp.setenv("AZURE_SPEECH_VOICE_NAME", test_voice)

            provider = get_tts_provider("azure")

            assert provider.endpoint == test_endpoint
            assert provider.subscription_key == test_key
            assert provider.voice_name == test_voice
