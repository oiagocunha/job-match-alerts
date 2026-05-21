from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.match import MatchResult


class JobSummary(BaseModel):
    external_id: str
    title: str
    company: str | None = None
    description: str = ""
    location: str | None = None
    url: str | None = None
    source: str = "import"
    seniority: str | None = None
    is_remote: bool | None = None


class JobRead(BaseModel):
    id: int
    external_id: str
    source: str
    title: str
    company: str | None
    description: str
    location: str | None
    salary_min: float | None
    salary_max: float | None
    url: str | None
    posted_at: str | None
    seniority: str | None
    is_remote: bool | None
    skills_analysis: dict[str, Any] | None
    synced_at: datetime

    model_config = {"from_attributes": True}


class JobImportRequest(BaseModel):
    url: str = Field(
        min_length=10,
        examples=["https://empresa.gupy.io/jobs/123456"],
        description="Link da vaga (Gupy, LinkedIn, Inhire ou página com descrição).",
    )


class JobImportResponse(BaseModel):
    job: JobRead
    match: MatchResult | None = None
    profile_required: bool = False


class JobAnalyzeRequest(BaseModel):
    description: str = Field(min_length=20)


class JobAnalyzeResponse(BaseModel):
    skills_required: list[str]
    skills_nice_to_have: list[str]
    seniority: str
    summary: str
    model: str
