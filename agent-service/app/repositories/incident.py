from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.incident import Incident
from app.models import IncidentModel


class IncidentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, incident: Incident) -> Incident:
        model = IncidentModel(
            id=incident.id,
            title=incident.title,
            description=incident.description,
            service=incident.service,
            severity=incident.severity,
            created_at=incident.created_at,
        )

        self.session.add(model)
        await self.session.flush()

        return incident

    async def get(self, incident_id: UUID) -> Incident | None:
        model = await self.session.get(
            IncidentModel,
            incident_id,
        )

        if model is None:
            return None

        return Incident(
            id=model.id,
            title=model.title,
            description=model.description,
            service=model.service,
            severity=model.severity,
            created_at=model.created_at,
        )