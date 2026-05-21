from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import CORS_ORIGINS, DATABASE_URL, database_host, database_url_source
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
    logging.info("DB config via %s, host=%s", database_url_source(), host)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with engine.connect() as conn:
            await run_migrations(conn)
    except Exception as exc:
        hint = (
            f"Falha ao conectar no Postgres (host={host!r}, via {database_url_source()}). "
            "Render: cadastre DB_HOST + DB_PASSWORD no painel (o .env do GitHub não entra no container). "
            "Supabase Session, porta 5432."
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
