# Performance Configuration for MiraMind Chatbot

# OpenAI API Settings
EMOTION_MODEL = "gpt-4o-mini"  # Faster model for emotion detection
RESPONSE_MODEL = "gpt-4o"  # Higher quality model for responses
MAX_TOKENS_EMOTION = 50  # Limit tokens for emotion detection
MAX_TOKENS_RESPONSE = 150  # Limit tokens for response generation
API_TIMEOUT = 10.0  # API timeout in seconds
TEMPERATURE = 0.7  # Response creativity level

# Context Management
MAX_CHAT_HISTORY = 4  # Number of previous messages to include
ENABLE_CACHING = True  # Enable response caching
MAX_CACHE_SIZE = 50  # Maximum number of cached responses

# Performance Features
ENABLE_ASYNC_TTS = True  # Use async TTS when available
ENABLE_ASYNC_LOGGING = True  # Use threaded logging
ENABLE_PARALLEL_PROCESSING = True  # Enable parallel processing where possible

# TTS Settings
TTS_PROVIDER = "azure"  # TTS provider to use
TTS_QUALITY = "standard"  # TTS quality level (standard/premium)

# File I/O
AUDIO_SAVE_ASYNC = True  # Save audio files asynchronously
LOG_LEVEL = "INFO"  # Logging level

# Memory Management
MEMORY_CLEANUP_INTERVAL = 100  # Clean memory every N requests
MAX_MEMORY_SIZE_MB = 100  # Maximum memory usage in MB
