from typing import Any, Optional

from typing_extensions import TypedDict


class ComplaintState(TypedDict, total=False):
    complaint_id: Optional[str]
    raw_text: str
    summary: Optional[dict[str, Any]]
    complaint_type: Optional[str]
    complaint_type_confidence: Optional[float]
    urgency: Optional[str]
    urgency_reason: Optional[str]
    rag_context: Optional[list[dict[str, Any]]]
    response_draft: Optional[str]
    error: Optional[str]
    current_step: Optional[str]
