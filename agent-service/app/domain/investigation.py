from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from app.domain.evidence import Evidence
from app.domain.hypothesis import Hypothesis


class InvestigationStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class InvestigationResult(BaseModel):
    evidence: list[Evidence]
    hypotheses: list[Hypothesis]

 
@dataclass
class Investigation:
    id: UUID
    incident_id: UUID
    status: InvestigationStatus
    created_at: datetime


@dataclass
class InvestigationEvent:
    id: UUID
    investigation_id: UUID
    event_type: str
    created_at: datetime