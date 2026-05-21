from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import CORS_ORIGINS, database_host, database_url_source
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
        hint = _db_connect_hint(host, database_url_source(), exc)
        logging.error("%s", hint)
        raise RuntimeError(hint) from exc


def _db_connect_hint(host: str | None, source: str, exc: BaseException) -> str:
    base = f"Falha ao conectar no Postgres (host={host!r}, via {source})."
    err = f"{type(exc).__name__}: {exc}".lower()
    if host and host.startswith("db.") and host.endswith(".supabase.co"):
        if "network is unreachable" in err or "errno 101" in err:
            return (
                f"{base} O host direto db.*.supabase.co é IPv6; Render free não alcança. "
                "Supabase → Connect → Session pooler: DB_HOST=aws-0-REGIAO.pooler.supabase.com, "
                "DB_USER=postgres.SEU_PROJECT_REF, DB_PORT=5432 (não use db.*.supabase.co no Render)."
            )
    return (
        f"{base} Confira DB_HOST/DB_PASSWORD no painel Render. "
        "Supabase no Render: Session pooler (pooler.supabase.com), porta 5432."
    )
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
