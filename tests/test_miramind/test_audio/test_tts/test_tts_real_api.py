import json
import os
import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from src.miramind.audio.tts.tts_factory import get_tts_provider


class TestTTSRealAPI:
    """
    Real API tests using actual Azure credentials.
    WARNING: These tests consume Azure tokens!
    """

    def setup_method(self):
        """Check if real API credentials are available."""
        self.endpoint = os.getenv("AZURE_SPEECH_ENDPOINT")
        self.key = os.getenv("AZURE_SPEECH_KEY")

        if not self.endpoint or not self.key:
            pytest.skip("Real Azure credentials not found in environment")

        if "test" in self.endpoint.lower() or "fake" in self.key.lower():
            pytest.skip("Test credentials detected, skipping real API tests")

    def test_basic_speech_synthesis(self):
        """Test basic speech synthesis with real API."""
        provider = get_tts_provider("azure")

        test_input = json.dumps(
            {"text": "Hello! This is a test of the Azure speech synthesis.", "emotion": "cheerful"}
        )

        # This should actually work with real credentials
        result = provider.synthesize(test_input)

        # Verify we got audio data back
        assert isinstance(result, bytes)
        assert len(result) > 0

        # Save to file for verification (optional)
        output_file = Path("test_output_basic.wav")
        with open(output_file, "wb") as f:
            f.write(result)
        print(f"✅ Audio saved to {output_file}")

    def test_emotional_speech_synthesis(self):
        """Test speech synthesis with different emotion."""
        provider = get_tts_provider("azure")

        test_input = json.dumps(
            {
                "text": "I'm feeling a bit sad today, but talking helps me feel better.",
                "emotion": "sad",
            }
        )

        result = provider.synthesize(test_input)

        # Verify we got audio data back
        assert isinstance(result, bytes)
        assert len(result) > 0

        # Save with emotion in filename
        output_file = Path("test_output_sad.wav")
        with open(output_file, "wb") as f:
            f.write(result)
        print(f"✅ Emotional audio saved to {output_file}")

    def teardown_method(self):
        """Clean up test files (optional)."""
        # You can comment this out if you want to keep the audio files
        test_files = ["test_output_basic.wav", "test_output_sad.wav"]
        for file in test_files:
            if Path(file).exists():
                print(f"🧹 Cleaned up {file}")
                # Path(file).unlink()  # Uncomment to actually delete files
