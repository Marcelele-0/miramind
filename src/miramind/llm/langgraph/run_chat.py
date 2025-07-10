import asyncio
import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Optional

from miramind.llm.langgraph.chatbot import get_chatbot
from miramind.llm.langgraph.performance_monitor import get_performance_monitor
from miramind.shared.logger import logger

logger.info("Logger works inside run_chat.py")

# Performance monitor
perf_monitor = get_performance_monitor()

# Thread pool for CPU-bound tasks - increased workers for better performance
executor = ThreadPoolExecutor(max_workers=4)

# Enhanced cache for repeated requests
response_cache = {}
MAX_CACHE_SIZE = 100  # Limit cache size


def _hash_input(user_input: str, emotion: str = "neutral") -> str:
    """Create a hash key for caching responses."""
    content = f"{user_input.lower().strip()}_{emotion}"
    return hashlib.md5(content.encode()).hexdigest()


def _cleanup_cache():
    """Remove oldest entries if cache is too large"""
    if len(response_cache) > MAX_CACHE_SIZE:
        # Remove oldest 20% of entries
        remove_count = len(response_cache) // 5
        oldest_keys = list(response_cache.keys())[:remove_count]
        for key in oldest_keys:
            del response_cache[key]


# Define the path where the output.wav should be saved inside frontend/public
OUTPUT_AUDIO_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "frontend", "public", "output.wav"
)
OUTPUT_AUDIO_PATH = os.path.abspath(OUTPUT_AUDIO_PATH)


def process_chat_message(user_input_text: str, chat_history: list = [], memory: str = ""):
    """
    Processes a single chat message using the chatbot and saves the response audio.
    Now with performance monitoring and enhanced caching.
    """
    with perf_monitor.track_operation("total_chat_processing"):
        state = {"chat_history": chat_history, "user_input": user_input_text, "memory": memory}

        # Check cache first
        with perf_monitor.track_operation("cache_lookup"):
            cache_key = _hash_input(user_input_text)
            if cache_key in response_cache:
                logger.info(f"Cache hit for key: {cache_key}")
                return response_cache[cache_key]

        try:
            with perf_monitor.track_operation("chatbot_invoke"):
                chatbot_instance = get_chatbot()
                state = chatbot_instance.invoke(state)

            response_text = state.get("response")
            audio_data = state.get("response_audio")
            updated_memory = state.get("memory", "")

            if audio_data:
                with perf_monitor.track_operation("audio_file_save"):
                    os.makedirs(os.path.dirname(OUTPUT_AUDIO_PATH), exist_ok=True)
                    with open(OUTPUT_AUDIO_PATH, "wb") as f:
                        f.write(audio_data)
                logger.info(f" Response audio saved to {OUTPUT_AUDIO_PATH}")
                result = {
                    "response_text": response_text,
                    "audio_file_path": OUTPUT_AUDIO_PATH,
                    "memory": updated_memory,
                }
            else:
                logger.info(" No audio generated.")
                result = {
                    "response_text": response_text,
                    "audio_file_path": None,
                    "memory": updated_memory,
                }

            # Update cache with cleanup
            with perf_monitor.track_operation("cache_update"):
                _cleanup_cache()  # Clean cache before adding
                response_cache[cache_key] = result
                logger.info(f"Response cached with key: {cache_key}")

            return result
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            return {
                "response_text": "I'm sorry, I couldn't process that.",
                "audio_file_path": None,
                "memory": memory,
            }


async def process_chat_message_async(
    user_input_text: str, chat_history: list = [], memory: str = ""
):
    """
    Async version of process_chat_message for better performance.
    """
    state = {"chat_history": chat_history, "user_input": user_input_text, "memory": memory}

    # Check cache first (async)
    cache_key = _hash_input(user_input_text)
    if cache_key in response_cache:
        logger.info(f"Cache hit (async) for key: {cache_key}")
        return response_cache[cache_key]

    try:
        # Run chatbot processing in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        chatbot_instance = get_chatbot()
        state = await loop.run_in_executor(executor, chatbot_instance.invoke, state)

        response_text = state.get("response")
        audio_data = state.get("response_audio")
        updated_memory = state.get("memory", "")

        if audio_data:
            # Run file I/O in thread pool
            await loop.run_in_executor(executor, _save_audio_file, audio_data)
            result = {
                "response_text": response_text,
                "audio_file_path": OUTPUT_AUDIO_PATH,
                "memory": updated_memory,
            }
        else:
            result = {
                "response_text": response_text,
                "audio_file_path": None,
                "memory": updated_memory,
            }

        # Update cache asynchronously
        await loop.run_in_executor(executor, _update_cache, cache_key, result)

        return result
    except Exception as e:
        logger.error(f"Error processing chat message (async): {e}")
        return {
            "response_text": "I'm sorry, I couldn't process that.",
            "audio_file_path": None,
            "memory": memory,
        }


def _save_audio_file(audio_data: bytes) -> None:
    """Helper function to save audio file."""
    os.makedirs(os.path.dirname(OUTPUT_AUDIO_PATH), exist_ok=True)
    with open(OUTPUT_AUDIO_PATH, "wb") as f:
        f.write(audio_data)


def _update_cache(cache_key: str, result: dict) -> None:
    """Helper function to update cache in thread pool."""
    _cleanup_cache()  # Clean cache before adding
    response_cache[cache_key] = result
    logger.info(f"Response cached with key: {cache_key}")


def main():
    if len(sys.argv) > 1:
        try:
            input_data = json.loads(sys.argv[1])
            user_input = input_data.get("text", "")
            chat_history_from_input = input_data.get("chat_history", [])
            memory_from_input = input_data.get("memory", "")

            result = process_chat_message(user_input, chat_history_from_input, memory_from_input)
            print(json.dumps(result))
        except json.JSONDecodeError:
            print("Error: Invalid JSON input.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"An error occurred: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Original interactive mode (optional, useful for testing standalone)
        print(" Emotion-Aware Contextual Chatbot for Neurodivergent Kids")
        print("Type 'exit' to quit.\n")

        current_chat_history = []
        memory = ""

        while True:
            user_input = input("Child: ").strip()
            if user_input.lower() in {"exit", "quit"}:
                print("Chatbot: It was great talking to you. Bye!")
                # Print performance statistics before exiting
                perf_monitor.print_stats()
                break

            result = process_chat_message(user_input, current_chat_history, memory)
            print("Chatbot:", result["response_text"])

            current_chat_history.append({"role": "user", "content": user_input})
            current_chat_history.append({"role": "assistant", "content": result["response_text"]})
            memory = result.get("memory", memory)

            if result["audio_file_path"]:
                logger.info(f"Audio file saved")
                print(f" Audio saved to {result['audio_file_path']}")

        # Show performance stats every 10 requests in interactive mode
        request_count = len(perf_monitor.metrics.get("total_chat_processing", []))
        if request_count > 0 and request_count % 10 == 0:
            perf_monitor.print_stats()


if __name__ == "__main__":
    main()
