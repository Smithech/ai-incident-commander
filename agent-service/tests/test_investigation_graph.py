import pytest
from uuid import UUID

from app.domain.evidence import Evidence
from app.domain.hypothesis import (
    HypothesisCandidate,
    HypothesisGenerationResult,
)
from app.services.hypothesis_generation import HypothesisGenerationInput
from app.workflows.investigation import (
    InvestigationState,
    build_investigation_graph,
    generate_hypotheses,
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


class FailingLLMClient:
    async def generate_hypotheses(
        self,
        request: HypothesisGenerationInput,
    ) -> HypothesisGenerationResult:
        raise AssertionError(
            "LLM should not be called when evidence is insufficient"
        )


class EmptyLLMClient:
    async def generate_hypotheses(
        self,
        request: HypothesisGenerationInput,
    ) -> HypothesisGenerationResult:
        return HypothesisGenerationResult(hypotheses=[])


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


def build_state() -> InvestigationState:
    return {
        "incident_id": UUID("00000000-0000-0000-0000-000000000001"),
        "service": "checkout-api",
        "incident_title": "Checkout errors increased",
        "incident_description": "Checkout errors increased significantly.",
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
    }


@pytest.mark.asyncio
async def test_generate_hypotheses_uses_llm_result() -> None:
    state = build_state()

    result = await generate_hypotheses(
        state,
        llm_client=FakeLLMClient(),
    )

    assert len(result["hypotheses"]) == 1

    hypothesis = result["hypotheses"][0]

    assert hypothesis.id
    assert hypothesis.statement == "Database pool exhaustion is possible."
    assert hypothesis.supporting_evidence_ids == ["evidence-1"]
    assert hypothesis.contradicting_evidence_ids == []


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
    )

    result = await graph.ainvoke(state)

    assert len(result["hypotheses"]) == 1

    hypothesis = result["hypotheses"][0]

    assert hypothesis.id
    assert hypothesis.statement == "Database pool exhaustion is possible."
    assert hypothesis.supporting_evidence_ids
    assert (
        hypothesis.supporting_evidence_ids[0]
        in {evidence.id for evidence in result["evidence"]}
    )


def test_should_end_when_evidence_is_empty():
    state = {
        "incident_id": UUID("00000000-0000-0000-0000-000000000001"),
        "service": "checkout-api",
        "incident_title": "Checkout latency increased",
        "incident_description": "Checkout API latency increased",
        "evidence": [],
        "hypotheses": [],
    }

    assert should_generate_hypotheses(state) == "end"


def test_should_generate_hypotheses_when_evidence_exists():
    state = {
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
    }

    assert should_generate_hypotheses(state) == "generate_hypotheses"


@pytest.mark.asyncio
async def test_investigation_graph_skips_llm_when_evidence_is_empty() -> None:
    state = build_state()
    state["evidence"] = []

    graph = build_investigation_graph(
        llm_client=FailingLLMClient(),
    )

    result = await graph.ainvoke(state)

    assert result["evidence"] == []
    assert result["hypotheses"] == []