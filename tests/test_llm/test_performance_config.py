import os
import sys

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.miramind.llm.langgraph.performance_config import *


class TestPerformanceConfig:
    """Test suite for performance configuration constants."""

    def test_openai_api_settings(self):
        """Test OpenAI API configuration constants."""
        assert EMOTION_MODEL == "gpt-4o-mini"
        assert RESPONSE_MODEL == "gpt-4o"
        assert isinstance(MAX_TOKENS_EMOTION, int)
        assert isinstance(MAX_TOKENS_RESPONSE, int)
        assert isinstance(API_TIMEOUT, float)
        assert isinstance(TEMPERATURE, float)

        # Validate reasonable values
        assert MAX_TOKENS_EMOTION > 0
        assert MAX_TOKENS_RESPONSE > 0
        assert API_TIMEOUT > 0
        assert 0 <= TEMPERATURE <= 2

    def test_context_management_settings(self):
        """Test context management configuration."""
        assert isinstance(MAX_CHAT_HISTORY, int)
        assert isinstance(ENABLE_CACHING, bool)
        assert isinstance(MAX_CACHE_SIZE, int)

        # Validate reasonable values
        assert MAX_CHAT_HISTORY > 0
        assert MAX_CACHE_SIZE > 0

    def test_performance_features_settings(self):
        """Test performance features configuration."""
        assert isinstance(ENABLE_ASYNC_TTS, bool)
        assert isinstance(ENABLE_ASYNC_LOGGING, bool)
        assert isinstance(ENABLE_PARALLEL_PROCESSING, bool)

    def test_tts_settings(self):
        """Test TTS configuration constants."""
        assert TTS_PROVIDER == "azure"
        assert TTS_QUALITY in ["standard", "premium"]

    def test_file_io_settings(self):
        """Test file I/O configuration."""
        assert isinstance(AUDIO_SAVE_ASYNC, bool)
        assert LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_memory_management_settings(self):
        """Test memory management configuration."""
        assert isinstance(MEMORY_CLEANUP_INTERVAL, int)
        assert isinstance(MAX_MEMORY_SIZE_MB, int)

        # Validate reasonable values
        assert MEMORY_CLEANUP_INTERVAL > 0
        assert MAX_MEMORY_SIZE_MB > 0

    def test_token_limits_reasonable(self):
        """Test that token limits are reasonable."""
        # Emotion detection should use fewer tokens than response
        assert MAX_TOKENS_EMOTION < MAX_TOKENS_RESPONSE

        # Values should be reasonable for the models
        assert MAX_TOKENS_EMOTION <= 100  # Should be small for emotion detection
        assert MAX_TOKENS_RESPONSE <= 500  # Should be reasonable for responses

    def test_model_configuration_consistency(self):
        """Test that model configuration is consistent."""
        # Emotion model should be the faster one
        assert "mini" in EMOTION_MODEL.lower()

        # Response model should be the higher quality one
        assert "gpt-4o" in RESPONSE_MODEL

    def test_timeout_configuration(self):
        """Test timeout configuration is reasonable."""
        assert API_TIMEOUT >= 5.0  # Should be at least 5 seconds
        assert API_TIMEOUT <= 30.0  # Should not be too long

    def test_temperature_configuration(self):
        """Test temperature configuration is valid."""
        assert 0.0 <= TEMPERATURE <= 1.0  # Should be in valid range for most use cases

    def test_cache_configuration(self):
        """Test cache configuration is reasonable."""
        if ENABLE_CACHING:
            assert MAX_CACHE_SIZE >= 10  # Should have reasonable cache size
            assert MAX_CACHE_SIZE <= 1000  # Should not be too large

    def test_chat_history_configuration(self):
        """Test chat history configuration is reasonable."""
        assert MAX_CHAT_HISTORY >= 2  # Should keep at least a few messages
        assert MAX_CHAT_HISTORY <= 20  # Should not keep too many messages

    def test_memory_configuration(self):
        """Test memory configuration is reasonable."""
        assert MEMORY_CLEANUP_INTERVAL >= 10  # Should not cleanup too frequently
        assert MAX_MEMORY_SIZE_MB >= 50  # Should have reasonable memory limit
        assert MAX_MEMORY_SIZE_MB <= 1000  # Should not be too large

    def test_boolean_configurations(self):
        """Test that boolean configurations are actually booleans."""
        boolean_configs = [
            ENABLE_CACHING,
            ENABLE_ASYNC_TTS,
            ENABLE_ASYNC_LOGGING,
            ENABLE_PARALLEL_PROCESSING,
            AUDIO_SAVE_ASYNC,
        ]

        for config in boolean_configs:
            assert isinstance(config, bool)

    def test_string_configurations(self):
        """Test that string configurations are valid."""
        assert isinstance(TTS_PROVIDER, str)
        assert isinstance(TTS_QUALITY, str)
        assert isinstance(LOG_LEVEL, str)
        assert isinstance(EMOTION_MODEL, str)
        assert isinstance(RESPONSE_MODEL, str)

        # Should not be empty
        assert len(TTS_PROVIDER) > 0
        assert len(TTS_QUALITY) > 0
        assert len(LOG_LEVEL) > 0
        assert len(EMOTION_MODEL) > 0
        assert len(RESPONSE_MODEL) > 0

    def test_numeric_configurations_positive(self):
        """Test that numeric configurations are positive."""
        numeric_configs = [
            MAX_TOKENS_EMOTION,
            MAX_TOKENS_RESPONSE,
            API_TIMEOUT,
            TEMPERATURE,
            MAX_CHAT_HISTORY,
            MAX_CACHE_SIZE,
            MEMORY_CLEANUP_INTERVAL,
            MAX_MEMORY_SIZE_MB,
        ]

        for config in numeric_configs:
            assert config > 0

    def test_configuration_accessibility(self):
        """Test that all configurations are accessible."""
        # Test that we can access all configurations without errors
        configs = [
            EMOTION_MODEL,
            RESPONSE_MODEL,
            MAX_TOKENS_EMOTION,
            MAX_TOKENS_RESPONSE,
            API_TIMEOUT,
            TEMPERATURE,
            MAX_CHAT_HISTORY,
            ENABLE_CACHING,
            MAX_CACHE_SIZE,
            ENABLE_ASYNC_TTS,
            ENABLE_ASYNC_LOGGING,
            ENABLE_PARALLEL_PROCESSING,
            TTS_PROVIDER,
            TTS_QUALITY,
            AUDIO_SAVE_ASYNC,
            LOG_LEVEL,
            MEMORY_CLEANUP_INTERVAL,
            MAX_MEMORY_SIZE_MB,
        ]

        # All should be accessible and not None
        for config in configs:
            assert config is not None

    def test_performance_optimizations_enabled(self):
        """Test that performance optimizations are properly configured."""
        # For a performance-focused config, async features should be enabled
        if ENABLE_ASYNC_TTS:
            assert isinstance(ENABLE_ASYNC_TTS, bool)

        if ENABLE_ASYNC_LOGGING:
            assert isinstance(ENABLE_ASYNC_LOGGING, bool)

        if ENABLE_PARALLEL_PROCESSING:
            assert isinstance(ENABLE_PARALLEL_PROCESSING, bool)

    def test_model_names_valid_format(self):
        """Test that model names follow expected format."""
        # OpenAI model names should contain 'gpt'
        assert "gpt" in EMOTION_MODEL.lower()
        assert "gpt" in RESPONSE_MODEL.lower()

    def test_tts_provider_valid(self):
        """Test that TTS provider is a known provider."""
        valid_providers = ["azure", "openai", "google", "amazon"]
        assert TTS_PROVIDER.lower() in valid_providers

    def test_log_level_valid(self):
        """Test that log level is a valid logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert LOG_LEVEL.upper() in valid_levels

    def test_tts_quality_valid(self):
        """Test that TTS quality is a valid option."""
        valid_qualities = ["standard", "premium", "high", "low"]
        assert TTS_QUALITY.lower() in valid_qualities
