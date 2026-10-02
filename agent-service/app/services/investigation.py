from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.domain.investigation import Investigation, InvestigationStatus
from app.repositories.investigation import InvestigationRepository


class InvestigationService:
    def __init__(self, repository: InvestigationRepository):
        self.repository = repository

    async def create_investigation(
        self,
        *,
        incident_id: UUID,
    ) -> Investigation:
        investigation = Investigation(
            id=uuid4(),
            incident_id=incident_id,
            status=InvestigationStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )

        await self.repository.create(investigation)

        await self.repository.add_event(
            investigation_id=investigation.id,
            event_type="investigation.created",
        )

        return investigation

    async def get_investigation(
        self,
        investigation_id: UUID,
    ) -> Investigation | None:
        return await self.repository.get(investigation_id)

    async def run_investigation(
        self,
        investigation_id: UUID,
    ) -> None:
        try:
            await self.repository.update_status(
                investigation_id,
                InvestigationStatus.RUNNING,
            )

            await self.repository.add_event(
                investigation_id=investigation_id,
                event_type="investigation.started",
            )

            await self.repository.session.commit()

            # Placeholder.
            # Más adelante aquí entrará el workflow de investigación.

            await self.repository.update_status(
                investigation_id,
                InvestigationStatus.COMPLETED,
            )

            await self.repository.add_event(
                investigation_id=investigation_id,
                event_type="investigation.completed",
            )

            await self.repository.session.commit()

        except Exception:
            await self.repository.session.rollback()

            await self.repository.update_status(
                investigation_id,
                InvestigationStatus.FAILED,
            )

            await self.repository.add_event(
                investigation_id=investigation_id,
                event_type="investigation.failed",
            )

            await self.repository.session.commit()

            raise