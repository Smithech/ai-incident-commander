from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class InvestigationModel(Base):
    __tablename__ = "investigations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(
        ForeignKey("incidents.id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    result: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )


class InvestigationEventModel(Base):
    __tablename__ = "investigation_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    investigation_id: Mapped[UUID] = mapped_column(
        ForeignKey("investigations.id"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    
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