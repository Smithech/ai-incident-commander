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