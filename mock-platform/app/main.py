from fastapi import FastAPI
from pydantic import BaseModel


class LogEntry(BaseModel):
    timestamp: str
    level: str
    service: str
    message: str


app = FastAPI(title="Mock Platform")


LOGS = [
    LogEntry(
        timestamp="2026-10-03T13:59:00Z",
        level="INFO",
        service="checkout-api",
        message="Request completed successfully",
    ),
    LogEntry(
        timestamp="2026-10-03T14:01:00Z",
        level="ERROR",
        service="checkout-api",
        message="Database connection timeout",
    ),
    LogEntry(
        timestamp="2026-10-03T14:02:00Z",
        level="ERROR",
        service="checkout-api",
        message="Failed to acquire database connection",
    ),
]


@app.get("/logs", response_model=list[LogEntry])
async def search_logs(
    service: str,
    query: str,
):
    return [
        log
        for log in LOGS
        if log.service == service
        and query.lower() in log.message.lower()
    ]