from datetime import datetime

from pydantic import BaseModel


class LogEntry(BaseModel):
    timestamp: str
    level: str
    service: str
    message: str


class MetricResult(BaseModel):
    metric: str
    service: str
    value: float
    baseline: float
    unit: str
    window_minutes: int


class Deployment(BaseModel):
    id: str
    service: str
    commit_sha: str
    deployed_at: datetime
    version: str


class Commit(BaseModel):
    sha: str
    message: str
    author: str
    changed_files: list[str]


class HistoricalIncident(BaseModel):
    id: str
    title: str
    root_cause: str
    resolved_at: datetime