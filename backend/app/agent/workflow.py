from langgraph.graph import END, START, StateGraph

from app.agent.state import ComplaintState
from app.agent.nodes import (
    classifier_node,
    rag_search_node,
    response_generator_node,
    summarizer_node,
    urgency_detector_node,
)


def build_workflow() -> StateGraph:
    """순차: summarizer → classifier → urgency_detector → rag_search → response_generator → END."""
    workflow = StateGraph(ComplaintState)

    workflow.add_node("summarizer", summarizer_node)
    workflow.add_node("classifier", classifier_node)
    workflow.add_node("urgency_detector", urgency_detector_node)
    workflow.add_node("rag_search", rag_search_node)
    workflow.add_node("response_generator", response_generator_node)

    workflow.add_edge(START, "summarizer")
    workflow.add_edge("summarizer", "classifier")
    workflow.add_edge("classifier", "urgency_detector")
    workflow.add_edge("urgency_detector", "rag_search")
    workflow.add_edge("rag_search", "response_generator")
    workflow.add_edge("response_generator", END)

    return workflow.compile()
