from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.services.dashboard_service import get_summary

router = APIRouter()


@router.get("/summary")
async def dashboard_summary(
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    session: AsyncSession = Depends(get_async_session),
):
    return await get_summary(session, from_date=from_date, to_date=to_date)
