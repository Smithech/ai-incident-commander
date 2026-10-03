from datetime import datetime

from pydantic import BaseModel, Field

    
class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    service: str
    message: str = Field(max_length=10_000)


class SearchLogsResult(BaseModel):
    matches: list[LogEntry] = Field(max_length=100)

