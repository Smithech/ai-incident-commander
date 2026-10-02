from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.investigation import (
    Investigation,
    InvestigationEvent,
    InvestigationStatus,
)
from app.models import InvestigationEventModel, InvestigationModel


class InvestigationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, investigation: Investigation) -> Investigation:
        model = InvestigationModel(
            id=investigation.id,
            incident_id=investigation.incident_id,
            status=investigation.status.value,
            created_at=investigation.created_at,
        )

        self.session.add(model)
        await self.session.flush()

        return investigation

    async def get(
        self,
        investigation_id: UUID,
    ) -> Investigation | None:
        model = await self.session.get(
            InvestigationModel,
            investigation_id,
        )

        if model is None:
            return None

        return Investigation(
            id=model.id,
            incident_id=model.incident_id,
            status=InvestigationStatus(model.status),
            created_at=model.created_at,
        )

    async def update_status(
        self,
        investigation_id: UUID,
        status: InvestigationStatus,
    ) -> None:
        model = await self.session.get(
            InvestigationModel,
            investigation_id,
        )

        if model is None:
            raise ValueError("Investigation not found")

        model.status = status.value

        await self.session.flush()

    async def add_event(
        self,
        *,
        investigation_id: UUID,
        event_type: str,
    ) -> InvestigationEvent:
        event = InvestigationEvent(
            id=uuid4(),
            investigation_id=investigation_id,
            event_type=event_type,
            created_at=datetime.now(timezone.utc),
        )

        self.session.add(
            InvestigationEventModel(
                id=event.id,
                investigation_id=event.investigation_id,
                event_type=event.event_type,
                created_at=event.created_at,
            )
        )

        await self.session.flush()

        return event