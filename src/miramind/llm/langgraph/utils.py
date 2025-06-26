import os
import json
import re
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

from miramind.audio.tts.tts_factory import get_tts_provider

# --- Load Environment ---
os.environ.pop("SSL_CERT_FILE", None)
load_dotenv()

# --- Constants ---
DEFAULT_MODEL = "gpt-4o"
LOG_FILE = "emotion_log.json"

# --- Client Init ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tts_provider = get_tts_provider("azure")

# --- Logger ---
class EmotionLogger:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def log(self, input_text: str, emotion: str, confidence: float, response_text: str = ""):
        entry = {
            "input": input_text,
            "emotion": emotion,
            "confidence": round(confidence, 2),
            "response": response_text
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

logger = EmotionLogger(LOG_FILE)

# --- API Helper ---
def call_openai(messages: List[Dict[str, str]], model: str = DEFAULT_MODEL) -> str:
    try:
        response = client.chat.completions.create(model=model, messages=messages)
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return ""

# --- Response Generator ---
def generate_response(style: str):
    def responder(state: Dict[str, Any]) -> Dict[str, Any]:
        user_input = state["user_input"]
        chat_history = state.get("chat_history", [])

        system_content = (
            f"You are a {style} non-licensed therapist who helps neurodivergent children talk about their feelings. "
            "Don't start every sentence by saying you're sorry or that you understand."
        )

        messages = [{"role": "system", "content": system_content}] + chat_history + [{"role": "user", "content": user_input}]
        reply = call_openai(messages)

        try:
            audio_bytes = tts_provider.synthesize(json.dumps({
                "text": reply,
                "emotion": state.get("emotion", "neutral")
            }))
        except Exception as e:
            print(f"TTS synthesis error: {e}")
            audio_bytes = None

        logger.log(
            input_text=user_input,
            emotion=state.get("emotion", "neutral"),
            confidence=state.get("emotion_confidence", 0.0),
            response_text=reply
        )

        return {
            **state,
            "response": reply,
            "response_audio": audio_bytes,
            "chat_history": chat_history + [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": reply}
            ]
        }
    return responder
