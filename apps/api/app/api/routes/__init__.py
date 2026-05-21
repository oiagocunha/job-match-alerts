from fastapi import APIRouter

from app.api.routes import alert_rules, integrations, jobs, match, profiles

api_router = APIRouter()
api_router.include_router(alert_rules.router)
api_router.include_router(integrations.router)
api_router.include_router(profiles.router)
api_router.include_router(jobs.router)
api_router.include_router(match.router)
