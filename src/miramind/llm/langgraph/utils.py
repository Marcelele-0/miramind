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
def call_openai(client: OpenAI, messages: List[Dict[str, str]], model: str = DEFAULT_MODEL) -> str:
    try:
        response = client.chat.completions.create(model=model, messages=messages)
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return ""


# --- Response Generator ---
def generate_response(style: str, client: OpenAI, tts_provider, emotion_logger: EmotionLogger):
    def responder(state: Dict[str, Any]) -> Dict[str, Any]:
        user_input = state["user_input"]
        chat_history = state.get("chat_history", [])
        logger.info(f"running response generator with style: {style}")

        system_content = (
            f"You are a {style} non-licensed therapist who helps neurodivergent children talk about their feelings. "
            "Don't start every sentence by saying you're sorry or that you understand."
        )

        messages = (
            [{"role": "system", "content": system_content}]
            + chat_history
            + [{"role": "user", "content": user_input}]
        )
        reply = call_openai(client, messages)

        try:
            audio_bytes = tts_provider.synthesize(
                json.dumps({"text": reply, "emotion": state.get("emotion", "neutral")})
            )
        except Exception as e:
            print(f"TTS synthesis error: {e}")
            audio_bytes = None

        emotion_logger.log(
            input_text=user_input,
            emotion=state.get("emotion", "neutral"),
            confidence=state.get("emotion_confidence", 0.0),
            response_text=reply,
        )
        logger.info(
            input_text=user_input,
            emotion=state.get("emotion", "neutral"),
            confidence=state.get("emotion_confidence", 0.0),
            response_text=reply,
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
