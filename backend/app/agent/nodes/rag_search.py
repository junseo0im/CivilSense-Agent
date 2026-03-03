import logging
from typing import Any

from app.agent.state import ComplaintState

logger = logging.getLogger(__name__)


async def rag_search_node(state: ComplaintState) -> dict[str, Any]:
    """ChromaDB에서 유사 민원 검색. 실패 시 빈 리스트로 진행."""
    try:
        from app.agent.rag import search_similar_complaints
    except ImportError:
        logger.warning("RAG module not available, skipping rag_search")
        return {"rag_context": [], "current_step": "rag_searched"}

    summary = state.get("summary")
    complaint_type = state.get("complaint_type") or ""
    if isinstance(summary, dict):
        query_text = "\n".join(f"{k}: {v}" for k, v in summary.items() if v) + f"\n유형: {complaint_type}"
    elif isinstance(summary, str):
        query_text = summary + f"\n유형: {complaint_type}"
    else:
        query_text = complaint_type or "민원"

    try:
        results = await search_similar_complaints(query_text, top_k=5)
        return {
            "rag_context": results,
            "current_step": "rag_searched",
        }
    except Exception as e:
        logger.warning("RAG search failed: %s, using empty context", e)
        return {"rag_context": [], "current_step": "rag_searched"}
