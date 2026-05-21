from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProfileStructured(BaseModel):
    name: str | None = None
    email: str | None = None
    headline: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience_years: dict[str, int] = Field(default_factory=dict)
    seniority: str = "unknown"
    languages: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experiences: list[dict[str, Any]] = Field(default_factory=list)


class ProfileSummary(BaseModel):
    id: int
    label: str
    name: str | None = None
    headline: str | None = None
    skills_count: int = 0
    seniority: str = "unknown"
    source_filename: str | None = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileRead(BaseModel):
    id: int
    demo_user_id: str
    label: str
    raw_text: str | None
    structured: ProfileStructured
    source_filename: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    label: str | None = Field(default=None, max_length=128)
    structured: ProfileStructured
    raw_text: str | None = Field(
        default=None,
        description="Texto integral do currículo (base lida pela IA / ATS).",
    )
