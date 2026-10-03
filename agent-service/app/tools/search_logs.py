from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from app.domain.evidence import Evidence

    
class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    service: str
    message: str = Field(max_length=10_000)


class SearchLogsResult(BaseModel):
    matches: list[LogEntry] = Field(max_length=100)


def search_logs_result_to_evidence(
    result: SearchLogsResult,
) -> list[Evidence]:
    evidence: list[Evidence] = []

    for index, log in enumerate(result.matches):
        evidence.append(
            Evidence(
                id=str(uuid4()),
                source="search_logs",
                summary=(
                    f"{log.level} log from {log.service}: "
                    f"{log.message}"
                ),
                data={
                    "timestamp": log.timestamp.isoformat(),
                    "level": log.level,
                    "service": log.service,
                    "message": log.message,
                },
            )
        )

    return evidence