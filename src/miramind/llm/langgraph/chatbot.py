# --- Imports ---
import os
import json
import re
from typing import List, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from openai import OpenAI

from miramind.audio.tts.tts_factory import get_tts_provider
from miramind.llm.langgraph.subgraphs import(
    build_sad_flow,
    build_angry_flow,
    build_excited_flow,
    build_gentle_flow,
    build_neutral_flow
)
from miramind.llm.langgraph.utils import (
    call_openai,
    logger,
)


# --- Load Environment ---
os.environ.pop("SSL_CERT_FILE", None)
load_dotenv()

# --- Config ---
DEFAULT_MODEL = "gpt-4o"
LOG_FILE = "emotion_log.json"
VALID_EMOTIONS = {"happy", "sad", "angry", "scared", "excited", "embarrassed", "anxious", "neutral"}
EMOTION_PROMPT = (
    "You are a non-licensed therapist specialized in neurodivergent children. "
    "You are great at recognizing children's emotions. "
    "Classify the following message as one of: happy, sad, angry, scared, excited, embarrassed, anxious, or neutral. "
    "Respond in JSON format like this: {\"emotion\": \"happy\", \"confidence\": 0.92} "
    "Adjust your response based on the child's emotional state. "
    "If you cannot determine the emotion, return neutral with confidence 0.0. "
    "Do not include any emojis."
)

# --- Clients ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tts_provider = get_tts_provider("azure")

# --- Models ---
class EmotionResult(BaseModel):
    emotion: str
    confidence: float

# --- Core Nodes ---
def detect_emotion(state: Dict[str, Any]) -> Dict[str, Any]:
    user_input = state["user_input"]

    messages = [
        {"role": "system", "content": EMOTION_PROMPT},
        {"role": "user", "content": user_input}
    ]

    raw = call_openai(messages)
    emotion, confidence = "neutral", 0.0

    try:
        match = re.search(r'{.*}', raw, re.DOTALL)
        if match:
            parsed = EmotionResult.parse_raw(match.group(0))
            if parsed.emotion in VALID_EMOTIONS:
                emotion = parsed.emotion
                confidence = parsed.confidence
    except ValidationError as e:
        print(f"Emotion parsing error: {e}")

    return {
        **state,
        "emotion": emotion,
        "emotion_confidence": confidence,
        "chat_history": state.get("chat_history", []) + [{"role": "user", "content": user_input}]
    }

def generate_response(style: str):
    def responder(state: Dict[str, Any]) -> Dict[str, Any]:
        user_input = state["user_input"]
        chat_history = state.get("chat_history", [])

        system_content = (
    f"You are a {style} non-licensed therapist who supports neurodivergent children in expressing and understanding their feelings. "
    "Engage with empathy, encouragement, and patience. "
    "Use age-appropriate, simple language. "
    "Focus on helping the child explore their emotions and offer gentle guidance. "
    "Avoid starting every sentence with apologies or statements like 'I understand.' "
    "Instead, ask open-ended questions and validate the child's experiences in a supportive way."
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


# --- Main LangGraph ---
main_graph = StateGraph(dict)

# Add emotion detection
main_graph.add_node("detect_emotion", RunnableLambda(detect_emotion))

# Add subgraphs for each emotional path
main_graph.add_node("sad_flow", build_sad_flow().compile())
main_graph.add_node("angry_flow", build_angry_flow().compile())
main_graph.add_node("excited_flow", build_excited_flow().compile())
main_graph.add_node("gentle_flow", build_gentle_flow().compile())
main_graph.add_node("neutral_flow", build_neutral_flow().compile())


# Set entry and conditional routing
main_graph.set_entry_point("detect_emotion")
main_graph.add_conditional_edges(
    "detect_emotion",
    lambda state: state.get("emotion", "neutral"),
    {
        "sad": "sad_flow",
        "angry": "angry_flow",
        "happy": "excited_flow",
        "excited": "excited_flow",
        "anxious": "gentle_flow",
        "embarrassed": "gentle_flow",
        "scared": "gentle_flow",
        "neutral": "neutral_flow"
    }
)

# --- Final Compiled Graph ---
chatbot = main_graph.compile()
