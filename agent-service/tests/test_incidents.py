from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.db import SessionFactory, init_db
from app.main import app
from app.models import (
    IncidentModel,
    InvestigationEventModel,
    InvestigationModel,
)


@pytest_asyncio.fixture(autouse=True)
async def clean_database():
    await init_db()
    yield

    async with SessionFactory() as session:
        await session.execute(delete(InvestigationEventModel))
        await session.execute(delete(InvestigationModel))
        await session.execute(delete(IncidentModel))
        await session.commit()


@pytest.mark.asyncio
async def test_create_and_get_incident_against_postgres():
    payload = {
        "title": "Checkout latency increased",
        "description": "Checkout API latency increased significantly",
        "service": "checkout-api",
        "severity": "critical",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post("/incidents", json=payload)

        assert create_response.status_code == 201
        created = create_response.json()
        incident_id = UUID(created["id"])

        get_response = await client.get(f"/incidents/{incident_id}")

    assert get_response.status_code == 200
    assert get_response.json() == created


@pytest.mark.asyncio
async def test_get_unknown_incident_returns_404():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/incidents/00000000-0000-0000-0000-000000000000"
        )

    assert response.status_code == 404
