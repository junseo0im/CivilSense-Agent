from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.services.complaint_service import complaint_service

router = APIRouter()


class RatingRequest(BaseModel):
    rating: int = Field(ge=1, le=5, description="1~5점 응답 만족도")
    feedback: str | None = Field(default=None, description="추가 코멘트 (선택)")


@router.post("", status_code=201)
async def create_complaint(
    body: dict[str, Any],
    session: AsyncSession = Depends(get_async_session),
):
    raw_text = (body.get("raw_text") or "").strip()
    if not raw_text:
        raise HTTPException(status_code=400, detail="raw_text is required and non-empty")
    result = await complaint_service.create_and_analyze(session, raw_text)
    return result


@router.get("")
async def list_complaints(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    complaint_type: str | None = Query(None),
    urgency: str | None = Query(None),
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    session: AsyncSession = Depends(get_async_session),
):
    items, total = await complaint_service.list_(
        session,
        page=page,
        page_size=page_size,
        status=status,
        complaint_type=complaint_type,
        urgency=urgency,
        from_date=from_date,
        to_date=to_date,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{id}")
async def get_complaint(
    id: int,
    session: AsyncSession = Depends(get_async_session),
):
    complaint = await complaint_service.get_by_id(session, id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {
        "id": complaint.id,
        "raw_text": complaint.raw_text,
        "summary": complaint.summary,
        "complaint_type": complaint.complaint_type,
        "complaint_type_confidence": complaint.complaint_type_confidence,
        "urgency": complaint.urgency,
        "urgency_reason": complaint.urgency_reason,
        "response_draft": complaint.response_draft,
        "response_rating": complaint.response_rating,
        "response_feedback": complaint.response_feedback,
        "status": complaint.status,
        "error_message": complaint.error_message,
        "created_at": complaint.created_at.isoformat() if complaint.created_at else None,
        "updated_at": complaint.updated_at.isoformat() if complaint.updated_at else None,
    }


@router.post("/{id}/rating")
async def set_rating(
    id: int,
    body: RatingRequest,
    session: AsyncSession = Depends(get_async_session),
):
    complaint = await complaint_service.set_rating(
        session,
        id=id,
        rating=body.rating,
        feedback=body.feedback,
    )
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {
        "complaint_id": complaint.id,
        "response_rating": complaint.response_rating,
        "response_feedback": complaint.response_feedback,
    }
