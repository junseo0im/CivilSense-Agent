import logging
from typing import Any

from app.agent.llm import chat, parse_json_from_text
from app.agent.state import ComplaintState

logger = logging.getLogger(__name__)

TYPES = "불편신고, 문의, 건의, 진정, 청구, 기타"

SYSTEM = "당신은 민원 유형을 분류하는 전문가입니다. JSON으로만 답변하세요."

USER_TEMPLATE = """다음 민원 요약과 원문 일부를 보고, 민원 유형을 하나만 선택하고 신뢰도(0~1)를 부여하세요.
유형 목록: {types}

요약:
{summary_text}

원문 일부:
{raw_preview}

다음 JSON 형식으로만 출력 (다른 설명 없이):
{{"type": "선택한 유형", "confidence": 0.95}}
"""


async def classifier_node(state: ComplaintState) -> dict[str, Any]:
    raw_text = state.get("raw_text") or ""
    summary = state.get("summary")
    summary_text = ""
    if isinstance(summary, dict):
        summary_text = "\n".join(f"{k}: {v}" for k, v in summary.items() if v)
    elif isinstance(summary, str):
        summary_text = summary
    raw_preview = (raw_text[:2000]) if raw_text else ""

    try:
        content = await chat(
            user_content=USER_TEMPLATE.format(
                types=TYPES,
                summary_text=summary_text or "(없음)",
                raw_preview=raw_preview,
            ),
            system_content=SYSTEM,
            temperature=0.2,
        )
        parsed = parse_json_from_text(content)
        if parsed and "type" in parsed:
            return {
                "complaint_type": str(parsed.get("type", "기타")),
                "complaint_type_confidence": float(parsed.get("confidence", 0.5)),
                "current_step": "classified",
            }
    except Exception as e:
        logger.exception("Classifier failed: %s", e)

    return {
        "complaint_type": "기타",
        "complaint_type_confidence": 0.0,
        "current_step": "classified",
    }
