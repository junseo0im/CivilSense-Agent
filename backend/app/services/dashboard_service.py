from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Complaint


async def get_summary(
    session: AsyncSession,
    from_date: str | None = None,
    to_date: str | None = None,
) -> dict[str, Any]:
    q = select(Complaint)
    if from_date:
        try:
            q = q.where(Complaint.created_at >= datetime.fromisoformat(from_date.replace("Z", "+00:00")))
        except ValueError:
            pass
    if to_date:
        try:
            q = q.where(Complaint.created_at <= datetime.fromisoformat(to_date.replace("Z", "+00:00")))
        except ValueError:
            pass

    by_type: dict[str, int] = {}
    by_urgency: dict[str, int] = {}
    by_status: dict[str, int] = {}
    total = 0

    rows = (await session.execute(q)).scalars().all()
    for c in rows:
        total += 1
        t = c.complaint_type or "기타"
        by_type[t] = by_type.get(t, 0) + 1
        u = c.urgency or "normal"
        by_urgency[u] = by_urgency.get(u, 0) + 1
        s = c.status or "pending"
        by_status[s] = by_status.get(s, 0) + 1

    return {
        "by_type": by_type,
        "by_urgency": by_urgency,
        "by_status": by_status,
        "total": total,
    }


dashboard_service = type("DashboardService", (), {"get_summary": staticmethod(get_summary)})()
