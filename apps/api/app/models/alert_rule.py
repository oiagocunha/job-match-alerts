from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # MVP: usuário fixo até auth (Fase 1+)
    demo_user_id: Mapped[str] = mapped_column(String(64), default="demo", index=True)
    name: Mapped[str] = mapped_column(String(120))
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    remote_only: Mapped[bool] = mapped_column(Boolean, default=False)
    min_score: Mapped[float] = mapped_column(Float, default=60.0)
    frequency: Mapped[str] = mapped_column(String(16), default="weekly")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
