from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.incidents import router as incidents_router
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="AI Incident Commander",
    lifespan=lifespan,
)

app.include_router(incidents_router)