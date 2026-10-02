from datetime import datetime, timezone
from uuid import uuid4

from app.domain.incident import Incident
from app.repositories.incident import IncidentRepository


class IncidentService:
    def __init__(self, repository: IncidentRepository):
        self.repository = repository

    async def create_incident(
        self,
        *,
        title: str,
        description: str,
        service: str,
        severity: str,
    ) -> Incident:
        incident = Incident(
            id=uuid4(),
            title=title,
            description=description,
            service=service,
            severity=severity,
            created_at=datetime.now(timezone.utc),
        )

        await self.repository.create(incident)

        return incident

    async def get_incident(
        self,
        incident_id,
    ) -> Incident | None:
        return await self.repository.get(incident_id)