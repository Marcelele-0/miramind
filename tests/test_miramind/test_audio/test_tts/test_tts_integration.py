import pytest
import json
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from src.miramind.audio.tts.tts_factory import get_tts_provider
from src.miramind.audio.tts.tts_base import TTSProvider


class TestTTSIntegration:
    """Practical integration tests for TTS functionality."""

    def test_factory_creates_working_provider(self):
        """Test that factory creates a functional TTS provider."""
        with pytest.MonkeyPatch().context() as mp:
            # Set test environment variables
            mp.setenv("AZURE_SPEECH_ENDPOINT", "https://test.api.cognitive.microsoft.com/")
            mp.setenv("AZURE_SPEECH_KEY", "test_key_12345")
            mp.setenv("AZURE_SPEECH_VOICE_NAME", "en-US-JennyNeural")
            
            # Factory should create provider without errors
            provider = get_tts_provider("azure")
            
            # Basic functionality checks
            assert provider is not None
            assert isinstance(provider, TTSProvider)
            assert hasattr(provider, 'synthesize')
            assert hasattr(provider, 'set_emotion')
            assert callable(provider.synthesize)
            assert callable(provider.set_emotion)

    def test_provider_handles_valid_json_input(self):
        """Test that provider processes valid JSON input correctly."""
        with pytest.MonkeyPatch().context() as mp:
            mp.setenv("AZURE_SPEECH_ENDPOINT", "https://test.api.cognitive.microsoft.com/")
            mp.setenv("AZURE_SPEECH_KEY", "test_key_12345")
            
            provider = get_tts_provider("azure")
            
            # Valid JSON input
            test_input = json.dumps({
                "text": "Hello, this is a test message!",
                "emotion": "cheerful"
            })
            
            # Should not raise an exception during parsing
            try:
                provider.synthesize(test_input)
            except (ValueError, json.JSONDecodeError):
                pytest.fail("Provider should handle valid JSON input without parsing errors")
            except Exception:
                # Other exceptions (like network/auth errors) are acceptable in tests
                pass

    def test_provider_rejects_invalid_json(self):
        """Test that provider properly validates JSON input."""
        with pytest.MonkeyPatch().context() as mp:
            mp.setenv("AZURE_SPEECH_ENDPOINT", "https://test.api.cognitive.microsoft.com/")
            mp.setenv("AZURE_SPEECH_KEY", "test_key_12345")
            
            provider = get_tts_provider("azure")
            
            # Invalid JSON should raise ValueError
            with pytest.raises(ValueError, match="Invalid JSON"):
                provider.synthesize("not valid json")

    def test_provider_requires_text_field(self):
        """Test that provider validates required 'text' field."""
        with pytest.MonkeyPatch().context() as mp:
            mp.setenv("AZURE_SPEECH_ENDPOINT", "https://test.api.cognitive.microsoft.com/")
            mp.setenv("AZURE_SPEECH_KEY", "test_key_12345")
            
            provider = get_tts_provider("azure")
            
            # JSON without 'text' field should raise ValueError
            invalid_input = json.dumps({"emotion": "happy"})
            with pytest.raises(ValueError, match="Missing 'text' field"):
                provider.synthesize(invalid_input)

    def test_provider_handles_different_emotions(self):
        """Test that provider accepts various emotion types."""
        with pytest.MonkeyPatch().context() as mp:
            mp.setenv("AZURE_SPEECH_ENDPOINT", "https://test.api.cognitive.microsoft.com/")
            mp.setenv("AZURE_SPEECH_KEY", "test_key_12345")
            
            provider = get_tts_provider("azure")
            
            # Test different emotions
            emotions_to_test = ["cheerful", "sad", "excited", "neutral", "angry"]
            
            for emotion in emotions_to_test:
                test_input = json.dumps({
                    "text": f"Testing {emotion} emotion",
                    "emotion": emotion
                })
                
                try:
                    provider.synthesize(test_input)
                except ValueError as e:
                    if "emotion" in str(e).lower():
                        pytest.fail(f"Provider should support {emotion} emotion")
                except Exception:
                    # Other exceptions (network, auth) are acceptable
                    pass

    def test_factory_error_handling(self):
        """Test that factory properly handles unknown providers."""
        with pytest.raises(ValueError, match="Unknown TTS provider"):
            get_tts_provider("nonexistent_provider")
        
        # Should list available providers in error message
        with pytest.raises(ValueError, match="Supported providers"):
            get_tts_provider("invalid")

    def test_abstract_base_prevents_direct_instantiation(self):
        """Test that TTSProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            TTSProvider()

    def test_provider_configuration_from_env(self):
        """Test that provider reads configuration from environment variables."""
        test_endpoint = "https://custom.api.cognitive.microsoft.com/"
        test_key = "custom_test_key_789"
        test_voice = "en-US-AriaNeural"
        
        with pytest.MonkeyPatch().context() as mp:
            mp.setenv("AZURE_SPEECH_ENDPOINT", test_endpoint)
            mp.setenv("AZURE_SPEECH_KEY", test_key)
            mp.setenv("AZURE_SPEECH_VOICE_NAME", test_voice)
            
            provider = get_tts_provider("azure")
            
            # Check that provider uses environment variables
            assert provider.endpoint == test_endpoint
            assert provider.subscription_key == test_key
            assert provider.voice_name == test_voice
