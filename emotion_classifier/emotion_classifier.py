from langgraph.graph import StateGraph
from typing import TypedDict
from nodes.nodes import emotion_classifier_node
import json

class EmotionState(TypedDict, total=False):  # Allow partial input
    transcript: str
    timestamps: list
    language: str
    emotion: str
    confidence: float

# Build graph
graph = StateGraph(dict)
graph.add_node("classify_emotion", emotion_classifier_node)

graph.set_entry_point("classify_emotion")
graph.set_finish_point("classify_emotion")

emotion_graph = graph.compile()

# Input data (In future will be replaced with data from talks with a kid)
input_data = {
    "transcript": "I feel tired today, but I want to have some fun",
    "timestamps": [],
    "language": "eng"
}

# Run classifier
result = emotion_graph.invoke(input_data)

# Save to JSON file
with open("emotion_result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=4)
