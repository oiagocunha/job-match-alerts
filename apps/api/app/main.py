from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import CORS_ORIGINS, DATABASE_URL, database_host
from app.db.base import Base
from app.db.migrate import run_migrations
from app.db.session import engine
from app.core.config import UPLOAD_DIR
from app.models import AlertRule, CandidateProfile, Job  # noqa: F401

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    host = database_host()
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with engine.connect() as conn:
            await run_migrations(conn)
    except Exception as exc:
        if host in ("postgres", "db"):
            hint = (
                "DATABASE_URL inválida: senha com ?, @ ou # precisa estar URL-encoded "
                "(no Supabase use o botão Copy na URI já codificada). "
                "Formato: postgresql+asyncpg://postgres:SENHA@db.xxxx.supabase.co:5432/postgres"
            )
        else:
            hint = (
                f"Não foi possível conectar ao Postgres (host={host!r}). "
                "Confira DATABASE_URL (Supabase: Session mode, postgresql+asyncpg://, host db.*.supabase.co)."
            )
        logging.error("%s", hint)
        raise RuntimeError(hint) from exc
    yield


app = FastAPI(
    title="Job Match Alerts API",
    description="Alertas de vagas e simulador ATS  case de portfólio.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
