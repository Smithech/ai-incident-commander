from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel

from app.db import SessionFactory
from app.domain.investigation import InvestigationResult
from app.repositories.incident import IncidentRepository
from app.repositories.investigation import InvestigationRepository
from app.services.investigation import InvestigationService
from app.services.llm import LLMClient, NvidiaLLMClient


router = APIRouter()


class InvestigationResponse(BaseModel):
    id: UUID
    incident_id: UUID
    status: str
    created_at: datetime
    result: InvestigationResult | None = None


def get_llm_client() -> LLMClient:
    return NvidiaLLMClient()


@router.post(
    "/incidents/{incident_id}/investigations",
    response_model=InvestigationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_investigation(
    incident_id: UUID,
    background_tasks: BackgroundTasks,
    llm_client: LLMClient = Depends(get_llm_client),
):
    async with SessionFactory() as session:
        incident_repository = IncidentRepository(session)

        incident = await incident_repository.get(incident_id)

        if incident is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found",
            )

        service = InvestigationService(
            repository=InvestigationRepository(session),
        )

        investigation = await service.create_investigation(
            incident_id=incident_id,
        )

        await session.commit()

    background_tasks.add_task(
        run_investigation,
        investigation.id,
        llm_client,
    )

    return investigation


@router.get(
    "/investigations/{investigation_id}",
    response_model=InvestigationResponse,
)
async def get_investigation(
    investigation_id: UUID,
):
    async with SessionFactory() as session:
        service = InvestigationService(
            repository=InvestigationRepository(session),
        )

        investigation = await service.get_investigation(
            investigation_id
        )

        if investigation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Investigation not found",
            )

        return investigation


async def run_investigation(
    investigation_id: UUID,
    llm_client: LLMClient,
) -> None:
    async with SessionFactory() as session:
        service = InvestigationService(
            InvestigationRepository(session)
        )

        await service.run_investigation(
            investigation_id,
            incident_repository=IncidentRepository(session),
            llm_client=llm_client,
        )