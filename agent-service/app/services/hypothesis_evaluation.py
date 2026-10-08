from pydantic import BaseModel, Field

from app.domain.evidence import Evidence
from app.domain.hypothesis import (
    Hypothesis,
    HypothesisEvaluationResult,
)


class HypothesisEvaluationInput(BaseModel):
    incident_service: str = Field(min_length=1, max_length=100)
    incident_title: str = Field(min_length=1, max_length=500)
    incident_description: str = Field(min_length=1, max_length=2_000)
    evidence: list[Evidence]
    hypotheses: list[Hypothesis]


async def evaluate_hypotheses(
    state,
    llm_client,
) -> dict:
    request = HypothesisEvaluationInput(
        incident_service=state["service"],
        incident_title=state["incident_title"],
        incident_description=state["incident_description"],
        evidence=state["evidence"],
        hypotheses=state["hypotheses"],
    )

    result = await llm_client.evaluate_hypotheses(request)

    validate_evaluation_references(
        result=result,
        evidence=state["evidence"],
        hypotheses=state["hypotheses"],
    )

    return {
        "evaluations": result.evaluations,
    }


def validate_evaluation_references(
    result: HypothesisEvaluationResult,
    evidence: list[Evidence],
    hypotheses: list[Hypothesis],
) -> None:
    valid_evidence_ids = {item.id for item in evidence}
    valid_hypothesis_ids = {item.id for item in hypotheses}

    for evaluation in result.evaluations:
        if evaluation.hypothesis_id not in valid_hypothesis_ids:
            raise ValueError(
                "Evaluation references unknown hypothesis ID: "
                f"{evaluation.hypothesis_id}"
            )

        referenced_evidence_ids = (
            evaluation.supporting_evidence_ids
            + evaluation.contradicting_evidence_ids
        )

        invalid_evidence_ids = (
            set(referenced_evidence_ids) - valid_evidence_ids
        )

        if invalid_evidence_ids:
            raise ValueError(
                "Evaluation references unknown evidence IDs: "
                + ", ".join(sorted(invalid_evidence_ids))
            )