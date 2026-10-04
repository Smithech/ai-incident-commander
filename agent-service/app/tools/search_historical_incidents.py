from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from app.domain.evidence import Evidence


class HistoricalIncident(BaseModel):
    id: str
    title: str
    root_cause: str
    resolved_at: datetime


class HistoricalIncidentsResult(BaseModel):
    incidents: list[HistoricalIncident] = Field(max_length=20)


def historical_incidents_to_evidence(
    result: HistoricalIncidentsResult,
) -> list[Evidence]:
    return [
        Evidence(
            id=str(uuid4()),
            source="search_historical_incidents",
            summary=(
                f"Historical incident {incident.id}: "
                f"{incident.title}. "
                f"Recorded root cause: {incident.root_cause}."
            ),
            data=incident.model_dump(mode="json"),
        )
        for incident in result.incidents
    ]