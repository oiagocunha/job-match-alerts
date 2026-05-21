from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

AlertFrequency = Literal["daily", "weekly"]


class AlertRuleBase(BaseModel):
    name: str = Field(min_length=1, max_length=120, examples=["Backend Python remoto"])
    keywords: str | None = Field(
        default=None,
        description="Palavras-chave separadas por vírgula.",
        examples=["python, fastapi, backend"],
    )
    remote_only: bool = False
    min_score: float = Field(default=60.0, ge=0, le=100)
    frequency: AlertFrequency = "weekly"
    is_active: bool = True


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    keywords: str | None = None
    remote_only: bool | None = None
    min_score: float | None = Field(default=None, ge=0, le=100)
    frequency: AlertFrequency | None = None
    is_active: bool | None = None


class AlertRuleRead(AlertRuleBase):
    id: int
    demo_user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
