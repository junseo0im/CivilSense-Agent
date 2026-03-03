from fastapi import APIRouter

from app.api import complaints, dashboard, qa

api_router = APIRouter(prefix="/api", tags=["api"])
api_router.include_router(complaints.router, prefix="/complaints", tags=["complaints"])
api_router.include_router(qa.router, prefix="/complaints", tags=["qa"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
