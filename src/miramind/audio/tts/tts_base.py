from abc import ABC, abstractmethod
from typing import Any


class TTSProvider(ABC):
    """
    Abstract base class for all Text-to-Speech providers.
    """

    @abstractmethod
    def synthesize(self, input_json: str) -> bytes:
        """
        Convert input text and emotion data into synthesized speech audio.

        Args:
            input_json (str): JSON string containing text and optional emotion data.
                               Expected format: {"text": "speech text", "emotion": "emotion_name"}

        Returns:
            bytes: Audio data in bytes format (typically MP3 or WAV)

        Raises:
            ValueError: If input_json is malformed or missing required fields
            NotImplementedError: If the method is not implemented by subclass
        """
        pass

    @abstractmethod
    def set_emotion(self, engine: Any, emotion: str) -> None:
        """
        Configure the TTS engine to reflect the specified emotion.

        Args:
            engine (Any): The TTS engine instance to configure
            emotion (str): The emotion to apply (e.g., 'happy', 'sad', 'neutral')

        Raises:
            NotImplementedError: If the method is not implemented by subclass
        """
        pass
