from enum import StrEnum

from pydantic import BaseModel, Field


class HypothesisCandidate(BaseModel):
    statement: str = Field(min_length=1, max_length=1_000)
    supporting_evidence_ids: list[str]
    contradicting_evidence_ids: list[str]


class HypothesisGenerationResult(BaseModel):
    hypotheses: list[HypothesisCandidate]


class Hypothesis(BaseModel):
    id: str
    statement: str = Field(min_length=1, max_length=1_000)
    supporting_evidence_ids: list[str]
    contradicting_evidence_ids: list[str]


class HypothesisVerdict(StrEnum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    INCONCLUSIVE = "inconclusive"


class HypothesisEvaluation(BaseModel):
    hypothesis_id: str
    verdict: HypothesisVerdict
    supporting_evidence_ids: list[str]
    contradicting_evidence_ids: list[str]
    reasoning: str = Field(min_length=1, max_length=2_000)


class HypothesisEvaluationResult(BaseModel):
    evaluations: list[HypothesisEvaluation]