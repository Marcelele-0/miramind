import os
from typing import Dict, Callable
from dotenv import load_dotenv
from miramind.audio.tts.tts_base import TTSProvider
from miramind.audio.tts.tts_azure import AzureTTSProvider
# Load environment variables
load_dotenv()


def get_tts_provider(name: str = "azure") -> TTSProvider:
    """
    Create and return a TTS provider instance based on the specified name.

    This factory function encapsulates the logic for instantiating different
    TTS providers, making it easy to add new providers without changing
    client code.

    Args:
        name (str): The name of the TTS provider to create (default: "azure")

    Returns:
        TTSProvider: An instance of the requested TTS provider

    Raises:
        ValueError: If the specified provider name is not supported

    Example:
        >>> json_input = '{"text": "Hello world", "emotion": "happy"}'
        >>> provider = get_tts_provider("azure")
        >>> audio = provider.synthesize(json_input)
    """
    provider_registry: Dict[str, Callable[[], TTSProvider]] = {
        "azure": lambda: AzureTTSProvider(
            # Using environment variables from .env file
            endpoint=os.getenv("AZURE_SPEECH_ENDPOINT"),
            subscription_key=os.getenv("AZURE_SPEECH_KEY"),
            voice_name=os.getenv("AZURE_SPEECH_VOICE_NAME", "en-US-JennyNeural")
        )
    }

    if name not in provider_registry:
        supported_providers = ", ".join(provider_registry.keys())
        raise ValueError(
            f"Unknown TTS provider: '{name}'. " f"Supported providers: {supported_providers}"
        )

    return provider_registry[name]()
