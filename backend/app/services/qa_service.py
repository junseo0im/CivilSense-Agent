import json
import logging

from app.agent.llm import chat
from app.db.models import Complaint

logger = logging.getLogger(__name__)

SYSTEM = "당신은 민원 문서를 검토한 담당자입니다. 주어진 요약과 원문 일부만을 근거로 질문에 답하세요. 모르는 내용은 추측하지 마세요."

USER_TEMPLATE = """[민원 요약]
{summary_text}

[원문 일부]
{raw_preview}

[질문]
{question}

위 내용을 바탕으로 질문에 간결하게 답변하세요."""


async def answer_question(complaint: Complaint, question: str) -> str:
    summary = complaint.summary
    if isinstance(summary, dict):
        summary_text = "\n".join(f"{k}: {v}" for k, v in summary.items() if v)
    else:
        summary_text = str(summary or "")
    raw_preview = (complaint.raw_text or "")[:3000]

    try:
        return await chat(
            user_content=USER_TEMPLATE.format(
                summary_text=summary_text,
                raw_preview=raw_preview,
                question=question,
            ),
            system_content=SYSTEM,
            temperature=0.3,
        )
    except Exception as e:
        logger.exception("QA failed: %s", e)
        return f"답변 생성 중 오류가 발생했습니다: {e}"
