# utils.py

import json
import os
import re
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from miramind.audio.tts.tts_factory import get_tts_provider
from miramind.shared.logger import logger

# --- Load Environment ---
os.environ.pop("SSL_CERT_FILE", None)
load_dotenv()

# --- Constants ---
DEFAULT_MODEL = "gpt-4o"
LOG_FILE = "emotion_log.json"


# --- Logger ---
class EmotionLogger:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def log(self, input_text: str, emotion: str, confidence: float, response_text: str = ""):
        entry = {
            "input": input_text,
            "emotion": emotion,
            "confidence": round(confidence, 2),
            "response": response_text,
        }
        try:
            if os.path.exists(self.filepath):
                with open(self.filepath, "r+", encoding="utf-8") as f:
                    data = json.load(f)
                    data.append(entry)
                    f.seek(0)
                    json.dump(data, f, indent=2)
            else:
                with open(self.filepath, "w", encoding="utf-8") as f:
                    json.dump([entry], f, indent=2)
        except Exception as e:
            print(f"Logging failed: {e}")


# --- API Helper ---
def call_openai(
    client: OpenAI,
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    max_tokens: int = None,
    temperature: float = 0.7,
) -> str:
    """
    Optimized OpenAI API call with better error handling and performance settings.
    """
    try:
        # Add performance optimizations
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=False,  # Disable streaming for faster single responses
            timeout=10.0,  # Add timeout to prevent hanging
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return ""


async def call_openai_async(
    client: OpenAI,
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    max_tokens: int = None,
    temperature: float = 0.7,
) -> str:
    """
    Async version of OpenAI API call for better concurrency.
    """
    try:
        # Use asyncio to run in executor for true async behavior
        import asyncio

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False,
                timeout=10.0,
            ),
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API error (async): {e}")
        return ""


# --- Response Generator ---
def generate_response(style: str, client: OpenAI, tts_provider, emotion_logger: EmotionLogger):
    def responder(state: Dict[str, Any]) -> Dict[str, Any]:
        user_input = state["user_input"]
        chat_history = state.get("chat_history", [])
        logger.info(f"running response generator with style: {style}")

        system_content = (
            f"You are a {style} non-licensed therapist who helps neurodivergent children talk about their feelings. "
            "Don't start every sentence by saying you're sorry or that you understand. "
            "Keep responses concise and engaging."  # Added for faster processing
        )

        messages = (
            [{"role": "system", "content": system_content}]
            + chat_history[-4:]  # Limit context to last 4 messages for faster processing
            + [{"role": "user", "content": user_input}]
        )
        reply = call_openai(client, messages, max_tokens=150, temperature=0.7)

        # Map emotions to TTS-supported emotions
        emotion_mapping = {
            "anxious": "scared",
            "embarrassed": "neutral",
            "excited": "excited",
            "happy": "happy",
            "sad": "sad",
            "angry": "angry",
            "scared": "scared",
            "neutral": "neutral",
        }

        detected_emotion = state.get("emotion", "neutral")
        tts_emotion = emotion_mapping.get(detected_emotion, "neutral")

        try:
            # Use async TTS if available
            if hasattr(tts_provider, 'synthesize_async'):
                import asyncio

                try:
                    loop = asyncio.get_event_loop()
                    audio_bytes = loop.run_until_complete(
                        tts_provider.synthesize_async(
                            json.dumps({"text": reply, "emotion": tts_emotion})
                        )
                    )
                except RuntimeError:
                    # Fallback to sync if no event loop
                    audio_bytes = tts_provider.synthesize(
                        json.dumps({"text": reply, "emotion": tts_emotion})
                    )
            else:
                audio_bytes = tts_provider.synthesize(
                    json.dumps({"text": reply, "emotion": tts_emotion})
                )
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            audio_bytes = None

        # Async logging to avoid blocking
        try:
            import threading

            log_thread = threading.Thread(
                target=emotion_logger.log,
                args=(
                    user_input,
                    state.get("emotion", "neutral"),
                    state.get("emotion_confidence", 0.0),
                    reply,
                ),
            )
            log_thread.daemon = True
            log_thread.start()
        except Exception as e:
            logger.error(f"Logging error: {e}")
        logger.info(
            f"Response generated - Emotion: {state.get('emotion', 'neutral')}, "
            f"Confidence: {state.get('emotion_confidence', 0.0)}, "
            f"Input: {user_input[:50]}{'...' if len(user_input) > 50 else ''}"
        )

        return {
            **state,
            "response": reply,
            "response_audio": audio_bytes,
            "chat_history": chat_history
            + [{"role": "user", "content": user_input}, {"role": "assistant", "content": reply}],
        }

    return responder


def main():
    """Initialize client, TTS provider, and emotion logger."""
    # --- Client Init ---
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    tts_provider = get_tts_provider("azure")
    emotion_logger = EmotionLogger(LOG_FILE)

    return client, tts_provider, emotion_logger


if __name__ == "__main__":
    client, tts_provider, emotion_logger = main()
