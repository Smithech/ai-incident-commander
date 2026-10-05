import pytest

from app.domain.evidence import Evidence
from app.domain.hypothesis import (
    HypothesisCandidate,
    HypothesisGenerationResult,
)
from app.services.hypothesis_generation import (
    HypothesisGenerationInput,
    validate_evidence_references,
)


def make_evidence(
    evidence_id: str,
    source: str,
) -> Evidence:
    return Evidence(
        id=evidence_id,
        source=source,
        summary=f"Evidence from {source}",
        data={},
    )


def test_valid_hypothesis_evidence_references_are_accepted():
    evidence = [
        make_evidence("evidence-1", "search_logs"),
        make_evidence("evidence-2", "query_metrics"),
    ]

    result = HypothesisGenerationResult(
        hypotheses=[
            HypothesisCandidate(
                statement="Database connection pool exhaustion is possible.",
                supporting_evidence_ids=[
                    "evidence-1",
                    "evidence-2",
                ],
                contradicting_evidence_ids=[],
            )
        ]
    )

    validate_evidence_references(result, evidence)


def test_unknown_hypothesis_evidence_reference_is_rejected():
    evidence = [
        make_evidence("evidence-1", "search_logs"),
    ]

    result = HypothesisGenerationResult(
        hypotheses=[
            HypothesisCandidate(
                statement="Database connection pool exhaustion is possible.",
                supporting_evidence_ids=[
                    "evidence-1",
                    "evidence-does-not-exist",
                ],
                contradicting_evidence_ids=[],
            )
        ]
    )

    with pytest.raises(
        ValueError,
        match="unknown evidence IDs",
    ):
        validate_evidence_references(result, evidence)


def test_empty_hypothesis_result_is_valid():
    evidence = [
        make_evidence("evidence-1", "search_logs"),
    ]

    result = HypothesisGenerationResult(
        hypotheses=[]
    )

    validate_evidence_references(result, evidence)


@pytest.mark.asyncio
async def test_llm_client_contract_returns_hypothesis_result():
    class FakeLLMClient:
        async def generate_hypotheses(
            self,
            request,
        ) -> HypothesisGenerationResult:
            return HypothesisGenerationResult(
                hypotheses=[
                    HypothesisCandidate(
                        statement="Database pool exhaustion is possible.",
                        supporting_evidence_ids=["evidence-1"],
                        contradicting_evidence_ids=[],
                    )
                ]
            )

    client = FakeLLMClient()

    request = HypothesisGenerationInput(
        incident_service="checkout-api",
        incident_title="Checkout failures",
        incident_description="Checkout requests are failing.",
        evidence=[
            make_evidence("evidence-1", "search_logs"),
        ],
    )

    result = await client.generate_hypotheses(request)

    assert len(result.hypotheses) == 1
    assert (
        result.hypotheses[0].supporting_evidence_ids
        == ["evidence-1"]
    )