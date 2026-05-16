from uuid import UUID

from pydantic import BaseModel


class BreakdownScores(BaseModel):
    spatial_score: int
    frequency_score: int


class VerifyResponse(BaseModel):
    verification_id: UUID
    trust_score: int
    verdict: str
    confidence: str
    processing_ms: int
    cached: bool
    billed_naira: int
    balance_remaining: int
    breakdown: BreakdownScores
