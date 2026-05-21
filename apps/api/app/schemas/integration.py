from pydantic import BaseModel


class IntegrationCheck(BaseModel):
    configured: bool
    ok: bool
    message: str


class IntegrationsStatusResponse(BaseModel):
    openai: IntegrationCheck
