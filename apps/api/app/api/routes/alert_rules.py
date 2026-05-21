from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.alert_rule import AlertRuleCreate, AlertRuleRead, AlertRuleUpdate
from app.schemas.common import HealthResponse
from app.services import alert_rules as alert_rules_service

router = APIRouter(tags=["Job Match Alerts"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
)
async def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok", service="job-match-alerts-api")


@router.get(
    "/alert-rules",
    response_model=list[AlertRuleRead],
    summary="Listar regras de alerta (demo)",
)
async def list_alert_rules_route(
    session: AsyncSession = Depends(get_session),
) -> list[AlertRuleRead]:
    rules = await alert_rules_service.list_alert_rules(session)
    return [AlertRuleRead.model_validate(rule) for rule in rules]


@router.post(
    "/alert-rules",
    response_model=AlertRuleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar regra de alerta",
)
async def create_alert_rule_route(
    payload: AlertRuleCreate,
    session: AsyncSession = Depends(get_session),
) -> AlertRuleRead:
    rule = await alert_rules_service.create_alert_rule(session, payload)
    return AlertRuleRead.model_validate(rule)


@router.get(
    "/alert-rules/{rule_id}",
    response_model=AlertRuleRead,
    summary="Obter regra por id",
)
async def get_alert_rule_route(
    rule_id: int,
    session: AsyncSession = Depends(get_session),
) -> AlertRuleRead:
    rule = await alert_rules_service.get_alert_rule(session, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regra não encontrada.")
    return AlertRuleRead.model_validate(rule)


@router.patch(
    "/alert-rules/{rule_id}",
    response_model=AlertRuleRead,
    summary="Atualizar regra de alerta",
)
async def update_alert_rule_route(
    rule_id: int,
    payload: AlertRuleUpdate,
    session: AsyncSession = Depends(get_session),
) -> AlertRuleRead:
    rule = await alert_rules_service.get_alert_rule(session, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regra não encontrada.")
    updated = await alert_rules_service.update_alert_rule(session, rule, payload)
    return AlertRuleRead.model_validate(updated)


@router.delete(
    "/alert-rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover regra de alerta",
)
async def delete_alert_rule_route(
    rule_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    rule = await alert_rules_service.get_alert_rule(session, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regra não encontrada.")
    await alert_rules_service.delete_alert_rule(session, rule)
