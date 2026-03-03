import json
import logging
from typing import Any

from app.agent.llm import chat, parse_json_from_text
from app.agent.state import ComplaintState

logger = logging.getLogger(__name__)

SYSTEM = "당신은 공공기관 민원 문서를 분석하는 전문가입니다. 요청된 형식에 맞춰 JSON으로만 답변하세요."

USER_TEMPLATE = """다음 민원 문서를 아래 항목으로 구조화하여 JSON 하나로 출력하세요. 다른 설명 없이 JSON만 출력합니다.

항목:
- 작성자정보: 작성자 관련 정보(있으면)
- 사건개요: 민원의 핵심 내용 요약
- 요청사항: 민원인이 요청하는 바
- 기타: 그 외 참고 사항

민원 문서:
---
{raw_text}
---
출력 형식 예시:
{{"작성자정보": "...", "사건개요": "...", "요청사항": "...", "기타": "..."}}
"""


async def summarizer_node(state: ComplaintState) -> dict[str, Any]:
    raw_text = (state.get("raw_text") or "").strip()
    if not raw_text:
        return {
            "summary": None,
            "error": "raw_text is empty",
            "current_step": "summarized",
        }

    try:
        content = await chat(
            user_content=USER_TEMPLATE.format(raw_text=raw_text[:15000]),
            system_content=SYSTEM,
            temperature=0.2,
        )
        summary = parse_json_from_text(content)
        if summary is None:
            summary = {"사건개요": content[:2000] if content else raw_text[:1000], "요청사항": "", "작성자정보": "", "기타": ""}
        return {
            "summary": summary,
            "current_step": "summarized",
        }
    except Exception as e:
        logger.exception("Summarizer failed: %s", e)
        return {
            "summary": {"사건개요": raw_text[:1000], "요청사항": "", "작성자정보": "", "기타": str(e)},
            "error": str(e),
            "current_step": "summarized",
        }
