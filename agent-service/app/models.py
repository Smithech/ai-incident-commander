from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class IncidentModel(Base):
    __tablename__ = "incidents"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    service: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(50))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )