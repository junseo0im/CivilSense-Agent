import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.pipeline import run_pipeline
from app.agent.rag import index_complaint
from app.db.models import Complaint

logger = logging.getLogger(__name__)


class ComplaintService:
    async def create_and_analyze(self, session: AsyncSession, raw_text: str) -> dict[str, Any]:
        """민원 저장(processing) → 파이프라인 실행 → 결과 업데이트 → RAG 인덱싱."""
        complaint = Complaint(
            raw_text=raw_text,
            status="processing",
        )
        session.add(complaint)
        await session.flush()
        await session.refresh(complaint)
        cid = complaint.id

        try:
            result = await run_pipeline(raw_text, complaint_id=str(cid))
        except Exception as e:
            logger.exception("Pipeline error for complaint %s: %s", cid, e)
            complaint.status = "failed"
            complaint.error_message = str(e)
            await session.commit()
            return {"complaint_id": cid, "status": "failed", "error_message": str(e)}

        summary = result.get("summary")
        complaint.summary = summary if isinstance(summary, dict) else None
        complaint.complaint_type = result.get("complaint_type")
        complaint.complaint_type_confidence = result.get("complaint_type_confidence")
        complaint.urgency = result.get("urgency")
        complaint.urgency_reason = result.get("urgency_reason")
        complaint.response_draft = result.get("response_draft") or ""
        complaint.error_message = result.get("error")
        complaint.status = "completed" if not result.get("error") else "failed"
        await session.commit()
        await session.refresh(complaint)

        if complaint.status == "completed" and complaint.summary and complaint.response_draft:
            summary_str = json.dumps(complaint.summary, ensure_ascii=False) if isinstance(complaint.summary, dict) else str(complaint.summary)
            index_complaint(
                complaint_id=complaint.id,
                summary_text=summary_str,
                complaint_type=complaint.complaint_type or "",
                response_snippet=complaint.response_draft[:500],
                urgency=complaint.urgency or "",
            )

        return self._to_response(complaint)

    def _to_response(self, c: Complaint) -> dict[str, Any]:
        return {
            "complaint_id": c.id,
            "status": c.status,
            "summary": c.summary,
            "complaint_type": c.complaint_type,
            "urgency": c.urgency,
            "response_draft": c.response_draft,
            "error_message": c.error_message,
            "response_rating": c.response_rating,
            "response_feedback": c.response_feedback,
        }

    async def get_by_id(self, session: AsyncSession, id: int) -> Complaint | None:
        r = await session.execute(select(Complaint).where(Complaint.id == id))
        return r.scalars().one_or_none()

    async def list_(
        self,
        session: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        complaint_type: str | None = None,
        urgency: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> tuple[list[dict], int]:
        q = select(Complaint)
        count_q = select(func.count()).select_from(Complaint)
        if status:
            q = q.where(Complaint.status == status)
            count_q = count_q.where(Complaint.status == status)
        if complaint_type:
            q = q.where(Complaint.complaint_type == complaint_type)
            count_q = count_q.where(Complaint.complaint_type == complaint_type)
        if urgency:
            q = q.where(Complaint.urgency == urgency)
            count_q = count_q.where(Complaint.urgency == urgency)
        if from_date:
            q = q.where(Complaint.created_at >= datetime.fromisoformat(from_date.replace("Z", "+00:00")))
            count_q = count_q.where(Complaint.created_at >= datetime.fromisoformat(from_date.replace("Z", "+00:00")))
        if to_date:
            q = q.where(Complaint.created_at <= datetime.fromisoformat(to_date.replace("Z", "+00:00")))
            count_q = count_q.where(Complaint.created_at <= datetime.fromisoformat(to_date.replace("Z", "+00:00")))

        total = (await session.execute(count_q)).scalar() or 0
        q = q.order_by(Complaint.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        rows = (await session.execute(q)).scalars().all()
        items = []
        for c in rows:
            items.append({
                "id": c.id,
                "raw_text_preview": (c.raw_text or "")[:200],
                "summary": c.summary,
                "complaint_type": c.complaint_type,
                "urgency": c.urgency,
                "status": c.status,
                "response_rating": c.response_rating,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            })
        return items, total

    async def set_rating(
        self,
        session: AsyncSession,
        id: int,
        rating: int,
        feedback: str | None = None,
    ) -> Complaint | None:
        """응답 품질 평점/피드백 저장."""
        complaint = await self.get_by_id(session, id)
        if not complaint:
            return None
        complaint.response_rating = rating
        complaint.response_feedback = feedback
        await session.commit()
        await session.refresh(complaint)
        return complaint


complaint_service = ComplaintService()
