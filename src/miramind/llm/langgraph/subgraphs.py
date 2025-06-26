from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from typing import Dict, Any

from miramind.llm.langgraph.utils import generate_response  


def build_sad_flow():
    graph = StateGraph(dict)
    graph.add_node("supportive_response", RunnableLambda(generate_response("supportive and caring")))

    def follow_up(state: Dict[str, Any]) -> Dict[str, Any]:
        followup = "Would you like to tell me more about what's making you feel this way?"
        return {
            **state,
            "response": state["response"] + " " + followup,
            "chat_history": state.get("chat_history", []) + [{"role": "assistant", "content": followup}]
        }

    graph.add_node("follow_up", RunnableLambda(follow_up))
    graph.set_entry_point("supportive_response")
    graph.add_edge("supportive_response", "follow_up")
    graph.add_edge("follow_up", END)
    return graph


def build_angry_flow():
    graph = StateGraph(dict)
    graph.add_node("calm_response", RunnableLambda(generate_response("calm and soothing")))
    graph.set_entry_point("calm_response")
    graph.add_edge("calm_response", END)
    return graph


def build_excited_flow():
    graph = StateGraph(dict)
    graph.add_node("enthusiastic_response", RunnableLambda(generate_response("enthusiastic and cheerful")))
    graph.set_entry_point("enthusiastic_response")
    graph.add_edge("enthusiastic_response", END)
    return graph


def build_gentle_flow():
    graph = StateGraph(dict)
    graph.add_node("gentle_response", RunnableLambda(generate_response("gentle and reassuring")))
    graph.set_entry_point("gentle_response")
    graph.add_edge("gentle_response", END)
    return graph


def build_neutral_flow():
    graph = StateGraph(dict)
    graph.add_node("neutral_response", RunnableLambda(generate_response("neutral and friendly")))
    graph.set_entry_point("neutral_response")
    graph.add_edge("neutral_response", END)
    return graph
