import logging
from typing import Any

from app.agent.state import ComplaintState
from app.agent.workflow import build_workflow

logger = logging.getLogger(__name__)

_compiled = None


def _get_compiled():
    global _compiled
    if _compiled is None:
        _compiled = build_workflow()
    return _compiled


async def run_pipeline(raw_text: str, complaint_id: str | None = None) -> dict[str, Any]:
    """민원 원문으로 파이프라인 실행. 최종 State 반환."""
    initial: ComplaintState = {
        "raw_text": raw_text,
        "complaint_id": complaint_id,
    }
    try:
        graph = _get_compiled()
        final = await graph.ainvoke(initial)
        return dict(final)
    except Exception as e:
        logger.exception("Pipeline failed: %s", e)
        return {
            **initial,
            "error": str(e),
            "current_step": "failed",
        }
