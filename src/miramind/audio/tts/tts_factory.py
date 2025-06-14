from typing import Dict, Callable
from miramind.audio.tts.tts_base import TTSProvider


def get_tts_provider(name: str = None) -> TTSProvider:
    """
    Create and return a TTS provider instance based on the specified name.

    This factory function encapsulates the logic for instantiating different
    TTS providers, making it easy to add new providers without changing
    client code.

    Args:
        name (str, optional): The name of the TTS provider to create.

    Returns:
        TTSProvider: An instance of the requested TTS provider

    Raises:
        ValueError: If the specified provider name is not supported

    Example:
        >>> json_input = '{"text": "Hello world", "emotion": "happy"}'
        >>> provider = get_tts_provider()
        >>> audio = provider.synthesize(json_input)
    """
    provider_registry: Dict[str, Callable[[], TTSProvider]] = {}

    if name not in provider_registry:
        supported_providers = ", ".join(provider_registry.keys())
        raise ValueError(
            f"Unknown TTS provider: '{name}'. " f"Supported providers: {supported_providers}"
        )

    return provider_registry[name]()
