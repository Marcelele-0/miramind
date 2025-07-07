from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from typing import Dict, Any

from miramind.llm.langgraph.utils import generate_response
from miramind.shared.logger import logger


def build_sad_flow():
    graph = StateGraph(dict)

    def supportive_responder(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Entered SAD flow")
        return generate_response("supportive and caring")(state)

    def follow_up(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(" SAD flow: adding follow-up message")
        followup = "Would you like to tell me more about what's making you feel this way?"
        return {
            **state,
            "response": state["response"] + " " + followup,
            "chat_history": state.get("chat_history", []) + [{"role": "assistant", "content": followup}]
        }

    graph.add_node("supportive_response", RunnableLambda(supportive_responder))
    graph.add_node("follow_up", RunnableLambda(follow_up))
    graph.set_entry_point("supportive_response")
    graph.add_edge("supportive_response", "follow_up")
    graph.add_edge("follow_up", END)
    return graph


def build_angry_flow():
    graph = StateGraph(dict)

    def calm_responder(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(" Entered ANGRY flow")
        return generate_response("calm and soothing")(state)

    graph.add_node("calm_response", RunnableLambda(calm_responder))
    graph.set_entry_point("calm_response")
    graph.add_edge("calm_response", END)
    return graph


def build_excited_flow():
    graph = StateGraph(dict)

    def enthusiastic_responder(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(" Entered EXCITED flow")
        return generate_response("enthusiastic and cheerful")(state)

    graph.add_node("enthusiastic_response", RunnableLambda(enthusiastic_responder))
    graph.set_entry_point("enthusiastic_response")
    graph.add_edge("enthusiastic_response", END)
    return graph


def build_gentle_flow():
    graph = StateGraph(dict)

    def gentle_responder(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(" Entered GENTLE flow")
        return generate_response("gentle and reassuring")(state)

    graph.add_node("gentle_response", RunnableLambda(gentle_responder))
    graph.set_entry_point("gentle_response")
    graph.add_edge("gentle_response", END)
    return graph


def build_neutral_flow():
    graph = StateGraph(dict)

    def neutral_responder(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(" Entered NEUTRAL flow")
        return generate_response("neutral and friendly")(state)

    graph.add_node("neutral_response", RunnableLambda(neutral_responder))
    graph.set_entry_point("neutral_response")
    graph.add_edge("neutral_response", END)
    return graph
