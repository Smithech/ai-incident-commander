from pydantic import BaseModel, Field

from app.domain.evidence import Evidence
from app.domain.hypothesis import (
    HypothesisCandidate,
    HypothesisGenerationResult,
)


class HypothesisGenerationInput(BaseModel):
    incident_service: str = Field(min_length=1, max_length=100)
    incident_title: str = Field(min_length=1, max_length=200)
    incident_description: str = Field(min_length=1, max_length=2_000)
    evidence: list[Evidence]


def validate_evidence_references(
    result: HypothesisGenerationResult,
    evidence: list[Evidence],
) -> None:
    valid_evidence_ids = {item.id for item in evidence}

    for hypothesis in result.hypotheses:
        referenced_ids = (
            hypothesis.supporting_evidence_ids
            + hypothesis.contradicting_evidence_ids
        )

        invalid_ids = set(referenced_ids) - valid_evidence_ids

        if invalid_ids:
            raise ValueError(
                "Hypothesis references unknown evidence IDs: "
                + ", ".join(sorted(invalid_ids))
            )