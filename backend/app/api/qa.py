from fastapi import APIRouter, Depends, HTTPException

from pydantic import BaseModel

from app.db.session import get_async_session
from app.services.complaint_service import complaint_service
from app.services.qa_service import answer_question
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class QaRequest(BaseModel):
    question: str


@router.post("/{id}/qa")
async def post_qa(
    id: int,
    body: QaRequest,
    session: AsyncSession = Depends(get_async_session),
):
    if not (body.question or "").strip():
        raise HTTPException(status_code=400, detail="question is required")
    complaint = await complaint_service.get_by_id(session, id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    answer = await answer_question(complaint, body.question.strip())
    return {"answer": answer}
