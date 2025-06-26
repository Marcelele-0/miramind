import pytest
from abc import ABC
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from src.miramind.audio.tts.tts_base import TTSProvider


class TestTTSProviderAbstract:
    """Simple tests for TTSProvider abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that TTSProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            TTSProvider()

    def test_concrete_implementation_works(self):
        """Test that concrete implementation can be created and used."""
        class MockTTSProvider(TTSProvider):
            def synthesize(self, input_json: str) -> bytes:
                return b"fake_audio_data"
            
            def set_emotion(self, engine, emotion: str) -> None:
                pass
        
        # Should be able to create and use
        provider = MockTTSProvider()
        result = provider.synthesize('{"text": "test"}')
        assert result == b"fake_audio_data"
        assert isinstance(provider, TTSProvider)

    def test_incomplete_implementation_fails(self):
        """Test that incomplete implementation cannot be instantiated."""
        class IncompleteTTSProvider(TTSProvider):
            def synthesize(self, input_json: str) -> bytes:
                return b"test"
            # Missing set_emotion method
        
        with pytest.raises(TypeError):
            IncompleteTTSProvider()
