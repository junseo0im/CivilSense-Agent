import os
from typing import Any

import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def _url(path: str) -> str:
    return f"{BACKEND_URL.rstrip('/')}{path}"


def post_complaint(raw_text: str) -> dict[str, Any]:
    """POST /api/complaints — 민원 접수 및 분석 (동기)."""
    with httpx.Client(timeout=120.0) as client:
        r = client.post(_url("/api/complaints"), json={"raw_text": raw_text})
        r.raise_for_status()
        return r.json()


def get_complaints(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    complaint_type: str | None = None,
    urgency: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> dict[str, Any]:
    """GET /api/complaints."""
    params: dict[str, Any] = {"page": page, "page_size": page_size}
    if status:
        params["status"] = status
    if complaint_type:
        params["complaint_type"] = complaint_type
    if urgency:
        params["urgency"] = urgency
    if from_date:
        params["from_date"] = from_date
    if to_date:
        params["to_date"] = to_date
    with httpx.Client(timeout=30.0) as client:
        r = client.get(_url("/api/complaints"), params=params)
        r.raise_for_status()
        return r.json()


def get_complaint(complaint_id: int) -> dict[str, Any]:
    """GET /api/complaints/:id."""
    with httpx.Client(timeout=30.0) as client:
        r = client.get(_url(f"/api/complaints/{complaint_id}"))
        r.raise_for_status()
        return r.json()


def post_qa(complaint_id: int, question: str) -> dict[str, Any]:
    """POST /api/complaints/:id/qa."""
    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            _url(f"/api/complaints/{complaint_id}/qa"),
            json={"question": question},
        )
        r.raise_for_status()
        return r.json()


def post_rating(complaint_id: int, rating: int, feedback: str | None = None) -> dict[str, Any]:
    """POST /api/complaints/:id/rating."""
    payload: dict[str, Any] = {"rating": rating}
    if feedback is not None and feedback.strip():
        payload["feedback"] = feedback.strip()
    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            _url(f"/api/complaints/{complaint_id}/rating"),
            json=payload,
        )
        r.raise_for_status()
        return r.json()


def get_dashboard_summary(
    from_date: str | None = None,
    to_date: str | None = None,
) -> dict[str, Any]:
    """GET /api/dashboard/summary."""
    params = {}
    if from_date:
        params["from_date"] = from_date
    if to_date:
        params["to_date"] = to_date
    with httpx.Client(timeout=30.0) as client:
        r = client.get(_url("/api/dashboard/summary"), params=params or None)
        r.raise_for_status()
        return r.json()
