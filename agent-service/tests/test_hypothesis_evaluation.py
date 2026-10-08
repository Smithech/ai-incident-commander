from uuid import uuid4

import pytest

from app.domain.evidence import Evidence
from app.domain.hypothesis import (
    Hypothesis,
    HypothesisEvaluation,
    HypothesisEvaluationResult,
    HypothesisVerdict,
)
from app.services.hypothesis_evaluation import (
    evaluate_hypotheses,
)


class FakeLLMClient:
    def __init__(
        self,
        result: HypothesisEvaluationResult,
    ):
        self.result = result
        self.received_request = None

    async def evaluate_hypotheses(self, request):
        self.received_request = request
        return self.result


@pytest.mark.asyncio
async def test_evaluate_hypotheses_returns_evaluation():
    evidence_id = str(uuid4())
    hypothesis_id = str(uuid4())

    evidence = Evidence(
        id=evidence_id,
        source="query_metrics",
        summary="Error rate is elevated.",
        data={
            "value": 15.8,
            "baseline": 0.7,
        },
    )

    hypothesis = Hypothesis(
        id=hypothesis_id,
        statement="The elevated error rate may be related to the external provider.",
        supporting_evidence_ids=[evidence_id],
        contradicting_evidence_ids=[],
    )

    llm_result = HypothesisEvaluationResult(
        evaluations=[
            HypothesisEvaluation(
                hypothesis_id=hypothesis_id,
                verdict=HypothesisVerdict.SUPPORTED,
                supporting_evidence_ids=[evidence_id],
                contradicting_evidence_ids=[],
                reasoning="The metric evidence supports the hypothesis.",
            )
        ]
    )

    llm_client = FakeLLMClient(llm_result)

    state = {
        "service": "checkout-api",
        "incident_title": "Elevated payment errors",
        "incident_description": "Checkout errors are above baseline.",
        "evidence": [evidence],
        "hypotheses": [hypothesis],
    }

    result = await evaluate_hypotheses(
        state,
        llm_client,
    )

    assert result["evaluations"] == llm_result.evaluations
    assert llm_client.received_request is not None
    assert llm_client.received_request.evidence == [evidence]
    assert llm_client.received_request.hypotheses == [hypothesis]


@pytest.mark.asyncio
async def test_evaluate_hypotheses_rejects_unknown_evidence_id():
    hypothesis_id = str(uuid4())

    hypothesis = Hypothesis(
        id=hypothesis_id,
        statement="The database may be causing the errors.",
        supporting_evidence_ids=[],
        contradicting_evidence_ids=[],
    )

    llm_result = HypothesisEvaluationResult(
        evaluations=[
            HypothesisEvaluation(
                hypothesis_id=hypothesis_id,
                verdict=HypothesisVerdict.SUPPORTED,
                supporting_evidence_ids=["unknown-evidence"],
                contradicting_evidence_ids=[],
                reasoning="Unsupported evaluation.",
            )
        ]
    )

    llm_client = FakeLLMClient(llm_result)

    state = {
        "service": "checkout-api",
        "incident_title": "Elevated errors",
        "incident_description": "The service is experiencing errors.",
        "evidence": [],
        "hypotheses": [hypothesis],
    }

    with pytest.raises(
        ValueError,
        match="unknown evidence IDs",
    ):
        await evaluate_hypotheses(
            state,
            llm_client,
        )