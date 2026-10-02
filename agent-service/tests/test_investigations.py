import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from uuid import UUID

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
async def test_create_investigation_lifecycle():
    incident_payload = {
        "title": "Checkout latency increased",
        "description": "Checkout API latency increased significantly",
        "service": "checkout-api",
        "severity": "critical",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        incident_response = await client.post(
            "/incidents",
            json=incident_payload,
        )

        assert incident_response.status_code == 201

        incident_id = UUID(
            incident_response.json()["id"]
        )

        investigation_response = await client.post(
            f"/incidents/{incident_id}/investigations"
        )

        assert investigation_response.status_code == 202

        investigation = investigation_response.json()

    investigation_id = UUID(investigation["id"])

    # El contrato HTTP devuelve la investigación recién creada.
    assert investigation["status"] == "pending"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        get_response = await client.get(
            f"/investigations/{investigation_id}"
        )

    assert get_response.status_code == 200
    assert get_response.json()["status"] == "completed"

    async with SessionFactory() as session:
        events = (
            await session.scalars(
                select(InvestigationEventModel)
                .where(
                    InvestigationEventModel.investigation_id
                    == investigation_id
                )
                .order_by(
                    InvestigationEventModel.created_at
                )
            )
        ).all()

    assert [event.event_type for event in events] == [
        "investigation.created",
        "investigation.started",
        "investigation.completed",
    ]


@pytest.mark.asyncio
async def test_create_investigation_requires_existing_incident():
    unknown_incident_id = UUID(
        "00000000-0000-0000-0000-000000000001"
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/incidents/{unknown_incident_id}/investigations"
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"


@pytest.mark.asyncio
async def test_get_unknown_investigation_returns_404():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/investigations/"
            "00000000-0000-0000-0000-000000000000"
        )

    assert response.status_code == 404