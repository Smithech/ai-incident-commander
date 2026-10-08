import pytest
from uuid import UUID

from app.domain.evidence import Evidence
from app.domain.hypothesis import (
    HypothesisCandidate,
    HypothesisGenerationResult,
    HypothesisEvaluation,
    HypothesisEvaluationResult,
    HypothesisVerdict,
)
from app.domain.tool_selection import ToolRequest, ToolSelectionResult
from app.services.hypothesis_evaluation import HypothesisEvaluationInput
from app.services.hypothesis_generation import HypothesisGenerationInput
from app.services.tool_selection import ToolSelectionInput
from app.workflows.investigation import (
    InvestigationState,
    build_investigation_graph,
    generate_hypotheses,
    InvestigationState,
    should_generate_hypotheses
)


class FakeLLMClient:
    async def generate_hypotheses(
        self,
        request: HypothesisGenerationInput,
    ) -> HypothesisGenerationResult:
        return HypothesisGenerationResult(
            hypotheses=[
                HypothesisCandidate(
                    statement="Database pool exhaustion is possible.",
                    supporting_evidence_ids=[request.evidence[0].id],
                    contradicting_evidence_ids=[],
                )
            ]
        )

    async def evaluate_hypotheses(
        self,
        request: HypothesisEvaluationInput,
    ) -> HypothesisEvaluationResult:
        hypothesis = request.hypotheses[0]
        evidence = request.evidence[0]

        return HypothesisEvaluationResult(
            evaluations=[
                HypothesisEvaluation(
                    hypothesis_id=hypothesis.id,
                    verdict=HypothesisVerdict.SUPPORTED,
                    supporting_evidence_ids=[evidence.id],
                    contradicting_evidence_ids=[],
                    reasoning="The evidence supports the hypothesis.",
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
        raise AssertionError(
            "LLM should not be called when evidence is insufficient"
        )

    async def evaluate_hypotheses(
        self,
        request: HypothesisEvaluationInput,
    ) -> HypothesisEvaluationResult:
        ...

    async def select_tools(
        self,
        request: ToolSelectionInput,
    ) -> ToolSelectionResult:
        return ToolSelectionResult(requests=[])


class ToolSelectingLLMClient:
    async def generate_hypotheses(
        self,
        request: HypothesisGenerationInput,
    ) -> HypothesisGenerationResult:
        return HypothesisGenerationResult(hypotheses=[])

    async def evaluate_hypotheses(
        self,
        request: HypothesisEvaluationInput,
    ) -> HypothesisEvaluationResult:
        ...

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
                        "query": "payment provider",
                    },
                ),
                ToolRequest(
                    tool_name="query_metrics",
                    arguments={
                        "service": request.incident_service,
                        "metric": "error_rate",
                        "window_minutes": 30,
                    },
                ),
            ],
        )


class EmptyLLMClient:
    async def generate_hypotheses(
        self,
        request: HypothesisGenerationInput,
    ) -> HypothesisGenerationResult:
        return HypothesisGenerationResult(hypotheses=[])

    async def evaluate_hypotheses(
        self,
        request: HypothesisEvaluationInput,
    ) -> HypothesisEvaluationResult:
            ...

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


class InvalidReferenceLLMClient:
    async def generate_hypotheses(
        self,
        request: HypothesisGenerationInput,
    ) -> HypothesisGenerationResult:
        return HypothesisGenerationResult(
            hypotheses=[
                HypothesisCandidate(
                    statement="This references unknown evidence.",
                    supporting_evidence_ids=["does-not-exist"],
                    contradicting_evidence_ids=[],
                )
            ]
        )

    async def evaluate_hypotheses(
        self,
        request: HypothesisEvaluationInput,
    ) -> HypothesisEvaluationResult:
        ...

    async def select_tools(
        self,
        request: ToolSelectionInput,
    ) -> ToolSelectionResult:
        return ToolSelectionResult(requests=[])


def build_state() -> InvestigationState:
    return {
        "incident_id": UUID("00000000-0000-0000-0000-000000000001"),
        "service": "checkout-api",
        "incident_title": "Checkout errors increased",
        "incident_description": "Checkout errors increased significantly.",
        "tool_requests": [],
        "evidence": [],
        "hypotheses": [],
        "evaluations": [],
    }


def build_state_with_evidence() -> InvestigationState:
    return {
        "incident_id": UUID("00000000-0000-0000-0000-000000000001"),
        "service": "checkout-api",
        "incident_title": "Checkout errors increased",
        "incident_description": "Checkout errors increased significantly.",
        "tool_requests": [],
        "evidence": [
            Evidence(
                id="evidence-1",
                source="query_metrics",
                summary="Checkout error rate increased.",
                data={
                    "metric": "error_rate",
                    "value": 18.4,
                    "baseline": 0.8,
                    "unit": "percent",
                },
            ),
        ],
        "hypotheses": [],
        "evaluations": [],
    }


async def fake_execute_tool(
    request: ToolRequest,
) -> list[Evidence]:
    return [
        Evidence(
            id="evidence-log-1",
            source="search_logs",
            summary="Database connection acquisition failures observed.",
            data={
                "message": "Failed to acquire database connection",
            },
        )
    ]


async def empty_execute_tool(
    request: ToolRequest,
) -> list[Evidence]:
    return []


@pytest.mark.asyncio
async def test_generate_hypotheses_uses_llm_result() -> None:
    state = build_state_with_evidence()

    result = await generate_hypotheses(
        state,
        llm_client=FakeLLMClient(),
    )

    assert len(result["hypotheses"]) == 1
    assert (
            result["hypotheses"][0].statement
            == "Database pool exhaustion is possible."
        )


@pytest.mark.asyncio
async def test_generate_hypotheses_allows_insufficient_evidence() -> None:
    state = build_state()

    result = await generate_hypotheses(
        state,
        llm_client=EmptyLLMClient(),
    )

    assert result["hypotheses"] == []


@pytest.mark.asyncio
async def test_generate_hypotheses_rejects_unknown_evidence_reference() -> None:
    state = build_state()

    with pytest.raises(
        ValueError,
        match="Hypothesis references unknown evidence IDs",
    ):
        await generate_hypotheses(
            state,
            llm_client=InvalidReferenceLLMClient(),
        )


@pytest.mark.asyncio
async def test_investigation_graph_generates_hypotheses() -> None:
    state = build_state()

    graph = build_investigation_graph(
        llm_client=FakeLLMClient(),
        execute_tool=fake_execute_tool,
    )

    result = await graph.ainvoke(state)

    assert len(result["evidence"]) == 1
    assert len(result["hypotheses"]) == 1
    assert len(result["evaluations"]) == 1

    assert (
        result["evaluations"][0].hypothesis_id == result["hypotheses"][0].id
    )


def test_should_end_when_evidence_is_empty():
    state: InvestigationState = {
        "incident_id": UUID("00000000-0000-0000-0000-000000000001"),
        "service": "checkout-api",
        "incident_title": "Checkout latency increased",
        "incident_description": "Checkout API latency increased",
        "tool_requests": [],
        "evidence": [],
        "hypotheses": [],
        "evaluations": [],
    }

    assert should_generate_hypotheses(state) == "end"


def test_should_generate_hypotheses_when_evidence_exists():
    
    state: InvestigationState = {
        "incident_id": UUID("00000000-0000-0000-0000-000000000001"),
        "service": "checkout-api",
        "incident_title": "Checkout latency increased",
        "incident_description": "Checkout API latency increased",
        "evidence": [
            Evidence(
                id="log-1",
                source="logs",
                summary="Database connection pool exhausted",
                data={
                    "message": "connection pool exhausted",
                },
            )
        ],
        "hypotheses": [],
        "tool_requests": [],
        "evaluations": [],
    }

    assert should_generate_hypotheses(state) == "generate_hypotheses"


@pytest.mark.asyncio
async def test_investigation_graph_completes_without_hypotheses_when_evidence_is_insufficient():
    state = build_state()

    graph = build_investigation_graph(
        llm_client=EmptyLLMClient(),
        execute_tool=empty_execute_tool,
    )

    result = await graph.ainvoke(state)

    assert result["evidence"] == []
    assert result["hypotheses"] == []
    assert result["evaluations"] == []