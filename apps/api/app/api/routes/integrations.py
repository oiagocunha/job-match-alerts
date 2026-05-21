from fastapi import APIRouter

from app.schemas.integration import IntegrationCheck, IntegrationsStatusResponse
from app.services import ai as ai_service

router = APIRouter(prefix="/integrations", tags=["Integrações"])


@router.get(
    "/status",
    response_model=IntegrationsStatusResponse,
    summary="Testar OpenAI",
)
async def integrations_status() -> IntegrationsStatusResponse:
    return IntegrationsStatusResponse(openai=await _check_openai())


async def _check_openai() -> IntegrationCheck:
    if not ai_service.is_configured():
        return IntegrationCheck(
            configured=False,
            ok=False,
            message="Defina OPENAI_API_KEY no .env",
        )
    try:
        summary = await ai_service.ping()
        return IntegrationCheck(
            configured=True,
            ok=True,
            message=f"OK  {summary[:120]}",
        )
    except ai_service.OpenAIError as exc:
        return IntegrationCheck(configured=True, ok=False, message=str(exc))
