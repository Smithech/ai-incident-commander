from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Incident:
    id: UUID
    title: str
    description: str
    service: str
    severity: str
    created_at: datetime