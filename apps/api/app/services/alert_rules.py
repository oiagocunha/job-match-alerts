from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert_rule import AlertRule
from app.schemas.alert_rule import AlertRuleCreate, AlertRuleUpdate

DEMO_USER_ID = "demo"


async def list_alert_rules(session: AsyncSession) -> list[AlertRule]:
    result = await session.execute(
        select(AlertRule)
        .where(AlertRule.demo_user_id == DEMO_USER_ID)
        .order_by(AlertRule.created_at.desc())
    )
    return list(result.scalars().all())


async def get_alert_rule(session: AsyncSession, rule_id: int) -> AlertRule | None:
    result = await session.execute(
        select(AlertRule).where(
            AlertRule.id == rule_id,
            AlertRule.demo_user_id == DEMO_USER_ID,
        )
    )
    return result.scalar_one_or_none()


async def create_alert_rule(session: AsyncSession, payload: AlertRuleCreate) -> AlertRule:
    rule = AlertRule(
        demo_user_id=DEMO_USER_ID,
        **payload.model_dump(),
    )
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule


async def update_alert_rule(
    session: AsyncSession,
    rule: AlertRule,
    payload: AlertRuleUpdate,
) -> AlertRule:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    await session.commit()
    await session.refresh(rule)
    return rule


async def delete_alert_rule(session: AsyncSession, rule: AlertRule) -> None:
    await session.delete(rule)
    await session.commit()
