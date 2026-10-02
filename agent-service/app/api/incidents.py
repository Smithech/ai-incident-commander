from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import SessionFactory
from app.repositories.incident import IncidentRepository
from app.services.incident import IncidentService

router = APIRouter()


class CreateIncidentRequest(BaseModel):
    title: str
    description: str
    service: str
    severity: str


class IncidentResponse(BaseModel):
    id: UUID
    title: str
    description: str
    service: str
    severity: str
    created_at: datetime


@router.post(
    "/incidents",
    response_model=IncidentResponse,
    status_code=201,
)
async def create_incident(
    request: CreateIncidentRequest,
):
    async with SessionFactory() as session:
        service = IncidentService(
            IncidentRepository(session)
        )

        incident = await service.create_incident(
            title=request.title,
            description=request.description,
            service=request.service,
            severity=request.severity,
        )

        await session.commit()

        return incident


@router.get(
    "/incidents/{incident_id}",
    response_model=IncidentResponse,
)
async def get_incident(incident_id: UUID):
    async with SessionFactory() as session:
        service = IncidentService(
            IncidentRepository(session)
        )

        incident = await service.get_incident(incident_id)

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident not found",
            )

        return incident