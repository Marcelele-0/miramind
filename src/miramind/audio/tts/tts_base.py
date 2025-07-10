from abc import ABC, abstractmethod


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
    def set_emotion(self, text: str, emotion: str) -> str:
        """
        Apply emotion to text and return properly formatted text for synthesis.

        This method should handle emotion application in a provider-specific way:
        - For SSML-based providers (Azure): return SSML markup with emotion tags
        - For other providers: return modified text or configuration string

        Args:
            text (str): The original text to synthesize
            emotion (str): The emotion to apply (e.g., 'happy', 'sad', 'neutral')

        Returns:
            str: Formatted text ready for synthesis (SSML, modified text, etc.)

        Raises:
            ValueError: If emotion is not supported by the provider
            NotImplementedError: If the method is not implemented by subclass
        """
        pass
    
