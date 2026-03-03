import logging
from typing import Any

from app.agent.llm import chat
from app.agent.state import ComplaintState

logger = logging.getLogger(__name__)

SYSTEM = """당신은 공공기관 민원 담당자입니다. 민원 내용을 반영한 정중하고 공식적인 응답 문 초안을 작성합니다.
유사 사례가 제공되면 톤과 처리 방식을 참고하되, 현재 민원에 맞게 작성하세요."""

USER_TEMPLATE = """다음 민원에 대한 공식 응답 문 초안을 작성하세요.

[민원 요약]
{summary_text}

[민원 유형] {complaint_type}
[긴급도] {urgency}
[긴급도 근거] {urgency_reason}

[참고: 유사 사례]
{rag_block}

위 내용을 바탕으로, 정중한 응답 문 초안을 작성해 주세요. (다른 설명 없이 응답 문만 출력)
"""


async def response_generator_node(state: ComplaintState) -> dict[str, Any]:
    summary = state.get("summary")
    complaint_type = state.get("complaint_type") or "기타"
    urgency = state.get("urgency") or "normal"
    urgency_reason = state.get("urgency_reason") or ""
    rag_context = state.get("rag_context") or []

    if isinstance(summary, dict):
        summary_text = "\n".join(f"{k}: {v}" for k, v in summary.items() if v)
    elif isinstance(summary, str):
        summary_text = summary
    else:
        summary_text = "(요약 없음)"

    rag_block = ""
    for i, item in enumerate(rag_context[:5], 1):
        s = item.get("summary") or item.get("document", "")
        r = item.get("response_snippet") or item.get("response_snippet", "")
        rag_block += f"--- 사례 {i} ---\n{s}\n응답 요약: {r}\n"

    if not rag_block:
        rag_block = "(유사 사례 없음)"

    try:
        content = await chat(
            user_content=USER_TEMPLATE.format(
                summary_text=summary_text,
                complaint_type=complaint_type,
                urgency=urgency,
                urgency_reason=urgency_reason,
                rag_block=rag_block,
            ),
            system_content=SYSTEM,
            temperature=0.5,
        )
        return {
            "response_draft": (content or "").strip(),
            "current_step": "response_generated",
        }
    except Exception as e:
        logger.exception("ResponseGenerator failed: %s", e)
        return {
            "response_draft": "",
            "error": state.get("error") or str(e),
            "current_step": "response_generated",
        }
