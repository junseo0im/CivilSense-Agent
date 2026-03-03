from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.types import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    complaint_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    complaint_type_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    urgency: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    urgency_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_draft: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
