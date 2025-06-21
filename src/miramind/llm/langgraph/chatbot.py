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

# Load environment variables and clear SSL settings
os.environ.pop("SSL_CERT_FILE", None)
load_dotenv()

# --- Configuration ---
DEFAULT_MODEL = "gpt-4o"
LOG_FILE = "emotion_log.json"
VALID_EMOTIONS = {"happy", "sad", "angry", "scared", "excited", "embarrassed", "anxious", "neutral"}
EMOTION_PROMPT = (
    "You are a non-licensed therapist specialized in neurodivergent children. "
    "You are great at recognizing children's emotions. "
    "Classify the following message as one of: happy, sad, angry, scared, excited, embarrassed, anxious, or neutral. "
    "Respond in JSON format like this: {\"emotion\": \"happy\", \"confidence\": 0.92}"
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tts_provider = get_tts_provider("azure")

# --- Models ---
class EmotionResult(BaseModel):
    emotion: str
    confidence: float

# --- Utilities ---
def call_openai(messages: List[Dict[str, str]], model: str = DEFAULT_MODEL) -> str:
    try:
        response = client.chat.completions.create(model=model, messages=messages)
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return ""

class EmotionLogger:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def log(self, input_text: str, emotion: str, confidence: float):
        entry = {"input": input_text, "emotion": emotion, "confidence": round(confidence, 2)}
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

# --- Graph Nodes ---
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

    logger.log(user_input, emotion, confidence)

    return {
        **state,
        "emotion": emotion,
        "emotion_confidence": confidence,
        "chat_history": state.get("chat_history", []) + [{"role": "user", "content": user_input}]
    }

def extract_facts(state: Dict[str, Any]) -> Dict[str, Any]:
    user_input = state["user_input"]
    facts = state.get("facts", {})

    messages = [
        {"role": "system", "content": "Extract any user facts from this message (like name, age, preferences) and return a JSON object."},
        {"role": "user", "content": user_input}
    ]

    try:
        raw = call_openai(messages)
        new_facts = json.loads(raw)
        if isinstance(new_facts, dict):
            facts.update(new_facts)
    except Exception as e:
        print(f"Fact extraction error: {e}")

    return {**state, "facts": facts}

def generate_response(style: str):
    def responder(state: Dict[str, Any]) -> Dict[str, Any]:
        user_input = state["user_input"]
        chat_history = state.get("chat_history", [])
        facts = state.get("facts", {})

        fact_summary = "\n".join([f"{k.capitalize()}: {v}" for k, v in facts.items()])
        system_content = (
            f"You are a {style} non-licensed therapist who helps neurodivergent children talk about their feelings.\n"
            f"Known facts about the user:\n{fact_summary if fact_summary else 'None yet.'}"
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

# --- Graph Construction ---
graph = StateGraph(dict)

# Add nodes
graph.add_node("detect_emotion", RunnableLambda(detect_emotion))
graph.add_node("extract_facts", RunnableLambda(extract_facts))
graph.add_node("calm_response", RunnableLambda(generate_response("calm and soothing")))
graph.add_node("enthusiastic_response", RunnableLambda(generate_response("enthusiastic and cheerful")))
graph.add_node("supportive_response", RunnableLambda(generate_response("supportive and caring")))
graph.add_node("gentle_response", RunnableLambda(generate_response("gentle and reassuring")))
graph.add_node("neutral_response", RunnableLambda(generate_response("neutral and friendly")))

# Entry point
graph.set_entry_point("detect_emotion")

# Add edge from emotion detection to fact extraction
graph.add_edge("detect_emotion", "extract_facts")

# Route based on emotion
graph.add_conditional_edges(
    "extract_facts",
    lambda state: state.get("emotion", "neutral"),
    {
        "angry": "calm_response",
        "happy": "enthusiastic_response",
        "excited": "enthusiastic_response",
        "sad": "supportive_response",
        "anxious": "gentle_response",
        "embarrassed": "gentle_response",
        "scared": "gentle_response",
        "neutral": "neutral_response"
    }
)

# Exit edges
for node in [
    "calm_response", "enthusiastic_response",
    "supportive_response", "gentle_response", "neutral_response"
]:
    graph.add_edge(node, END)

chatbot = graph.compile()
