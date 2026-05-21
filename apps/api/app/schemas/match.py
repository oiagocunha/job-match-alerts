from pydantic import BaseModel, Field


class MatchBreakdown(BaseModel):
    skills: float
    seniority: float
    experience: float
    semantic_match: float


class MatchResult(BaseModel):
    score: float
    breakdown: MatchBreakdown
    matched: list[str]
    missing: list[str]
    job_seniority: str
    candidate_seniority: str
    explanation: list[str]


class RankedJobMatch(BaseModel):
    job_id: int
    title: str
    company: str | None
    source: str
    url: str | None
    is_remote: bool | None
    seniority: str | None
    match: MatchResult


class MatchRankResponse(BaseModel):
    results: list[RankedJobMatch]
    profile_required: bool = False


class MatchJobRequest(BaseModel):
    analyze_if_needed: bool = Field(
        default=True,
        description="Extrai skills da vaga com OpenAI se ainda não existir análise.",
    )
