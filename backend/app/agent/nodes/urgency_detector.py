import logging
import re
from typing import Any

from app.agent.llm import chat, parse_json_from_text
from app.agent.state import ComplaintState

logger = logging.getLogger(__name__)

URGENT_KEYWORDS = re.compile(
    r"파손|사고|위험|긴급|즉시|응급|침수|화재|붕괴|낙하|유독|유해|생명|위급",
    re.IGNORECASE,
)

SYSTEM = "당신은 민원 긴급도를 판단하는 전문가입니다. urgent / normal / low 중 하나와 짧은 근거만 JSON으로 답변하세요."

USER_TEMPLATE = """다음 민원 요약과 원문 일부를 보고, 긴급도를 판단하세요.
- urgent: 즉시 대응이 필요한 경우 (안전 사고, 위험, 긴급 등)
- normal: 일반적인 처리 기한 내 대응
- low: 여유 있는 문의·건의

요약:
{summary_text}

원문 일부:
{raw_preview}

다음 JSON 형식으로만 출력:
{{"urgency": "urgent 또는 normal 또는 low", "reason": "한 줄 근거"}}
"""


async def urgency_detector_node(state: ComplaintState) -> dict[str, Any]:
    raw_text = state.get("raw_text") or ""
    summary = state.get("summary")
    summary_text = ""
    if isinstance(summary, dict):
        summary_text = "\n".join(f"{k}: {v}" for k, v in summary.items() if v)
    elif isinstance(summary, str):
        summary_text = summary
    raw_preview = (raw_text[:3000]) if raw_text else ""
    combined = f"{summary_text}\n{raw_preview}"

    # 규칙: 긴급 키워드 있으면 urgent 후보
    rule_urgent = bool(URGENT_KEYWORDS.search(combined))

    try:
        content = await chat(
            user_content=USER_TEMPLATE.format(
                summary_text=summary_text or "(없음)",
                raw_preview=raw_preview,
            ),
            system_content=SYSTEM,
            temperature=0.2,
        )
        parsed = parse_json_from_text(content)
        if parsed and "urgency" in parsed:
            urgency = str(parsed.get("urgency", "normal")).lower()
            if urgency not in ("urgent", "normal", "low"):
                urgency = "normal"
            reason = str(parsed.get("reason", ""))
            if rule_urgent and urgency == "normal":
                urgency = "urgent"
                reason = reason or "키워드 기반 긴급 판단"
            return {
                "urgency": urgency,
                "urgency_reason": reason,
                "current_step": "urgency_done",
            }
    except Exception as e:
        logger.exception("UrgencyDetector failed: %s", e)

    return {
        "urgency": "urgent" if rule_urgent else "normal",
        "urgency_reason": "자동 판단 실패" if not rule_urgent else "키워드 기반 긴급 판단",
        "current_step": "urgency_done",
    }
