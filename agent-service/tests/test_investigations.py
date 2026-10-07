from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.api.investigations import get_llm_client
from app.db import SessionFactory
from app.domain.evidence import Evidence
from app.domain.hypothesis import (
    HypothesisCandidate,
    HypothesisGenerationResult,
)
from app.domain.tool_selection import ToolRequest, ToolSelectionResult
from app.main import app
from app.models import (
    IncidentModel,
    InvestigationEventModel,
    InvestigationModel,
)
from app.repositories.incident import IncidentRepository
from app.repositories.investigation import InvestigationRepository
from app.services.hypothesis_generation import HypothesisGenerationInput
from app.services.investigation import InvestigationService
from app.services.tool_selection import ToolSelectionInput


class FakeLLMClient:
    async def generate_hypotheses(
        self,
        request: HypothesisGenerationInput,
    ) -> HypothesisGenerationResult:
        evidence_id = request.evidence[0].id

        return HypothesisGenerationResult(
            hypotheses=[
                HypothesisCandidate(
                    statement=(
                        "The checkout service is experiencing "
                        "database-related failures."
                    ),
                    supporting_evidence_ids=[evidence_id],
                    contradicting_evidence_ids=[],
                )
            ]
        )

    async def select_tools(
        self,
        request: ToolSelectionInput,
    ) -> ToolSelectionResult:
        return ToolSelectionResult(
            requests=[
                ToolRequest(
                    tool_name="search_logs",
                    arguments={
                        "service": request.incident_service,
                        "query": "database",
                    },
                )
            ]
        )


class FailingLLMClient:
    async def generate_hypotheses(
        self,
        request: HypothesisGenerationInput,
    ) -> HypothesisGenerationResult:
        raise RuntimeError("LLM failure")

    async def select_tools(
        self,
        request: ToolSelectionInput,
    ) -> ToolSelectionResult:
        return ToolSelectionResult(
            requests=[
                ToolRequest(
                    tool_name="search_logs",
                    arguments={
                        "service": request.incident_service,
                        "query": "database",
                    },
                )
            ]
        )


async def fake_execute_tool(
    request: ToolRequest,
) -> list[Evidence]:
    return [
        Evidence(
            id="evidence-test-1",
            source="search_logs",
            summary="Database connection acquisition failures observed.",
            data={
                "message": "Failed to acquire database connection",
            },
        )
    ]


@pytest_asyncio.fixture(autouse=True)
async def clean_database():
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

    app.dependency_overrides[get_llm_client] = lambda: FakeLLMClient()

    try:
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

        investigation_response = get_response.json()

        assert get_response.json()["status"] == "completed"
        assert investigation_response["result"] is not None

        result = investigation_response["result"]

        assert "evidence" in result
        assert "hypotheses" in result

        assert len(result["evidence"]) > 0
        assert len(result["hypotheses"]) > 0

        async with SessionFactory() as session:
            investigation_model = await session.get(
                InvestigationModel,
                investigation_id,
            )

        assert investigation_model is not None
        assert investigation_model.result is not None

        assert "evidence" in investigation_model.result
        assert "hypotheses" in investigation_model.result

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
        
    finally:
            app.dependency_overrides.clear()    


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


@pytest.mark.asyncio
async def test_investigation_failure_persists_failed_state_without_result():
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

    async with SessionFactory() as session:
        service = InvestigationService(
            repository=InvestigationRepository(session),
        )

        investigation = await service.create_investigation(
            incident_id=incident_id,
        )

        await session.commit()

        investigation_id = investigation.id

    async with SessionFactory() as session:
        service = InvestigationService(
            repository=InvestigationRepository(session),
        )

        with pytest.raises(RuntimeError, match="LLM failure"):
            await service.run_investigation(
                investigation_id,
                incident_repository=IncidentRepository(session),
                llm_client=FailingLLMClient(),
                execute_tool=fake_execute_tool,
            )

    async with SessionFactory() as session:
        repository = InvestigationRepository(session)

        investigation = await repository.get(
            investigation_id
        )

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

    assert investigation is not None
    assert investigation.status.value == "failed"
    assert investigation.result is None

    assert [event.event_type for event in events] == [
        "investigation.created",
        "investigation.started",
        "investigation.failed",
    ]