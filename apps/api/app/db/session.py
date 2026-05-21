from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import DATABASE_URL, database_host, normalize_database_url

_db_url = normalize_database_url(DATABASE_URL)
if "+asyncpg" not in _db_url:
    raise RuntimeError(
        "DATABASE_URL deve usar o driver asyncpg, ex.: postgresql+asyncpg://user:pass@host:5432/db "
        "(Supabase: troque postgresql:// por postgresql+asyncpg:// no Render).",
    )

_host = database_host() or ""
_connect_args: dict = {}
if _host and (
    ".render.com" in _host
    or "supabase.co" in _host
    or "pooler.supabase.com" in _host
    or "neon.tech" in _host
):
    _connect_args["ssl"] = True

engine = create_async_engine(_db_url, echo=False, connect_args=_connect_args)
SessionLocal = async_sessionmaker[AsyncSession](engine, expire_on_commit=False)
