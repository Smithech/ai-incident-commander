from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.incidents import router as incidents_router
from app.api.investigations import router as investigations_router


app = FastAPI(
    title="AI Incident Commander",
)

app.include_router(incidents_router)
app.include_router(investigations_router)