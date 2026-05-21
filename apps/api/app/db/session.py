import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import DATABASE_URL, database_host, normalize_database_url

def _url_for_asyncpg(url: str) -> str:
    """asyncpg não aceita sslmode= na query string — só connect_args ssl."""
    if "?" in url:
        base, _, query = url.partition("?")
        if "sslmode" in query or "ssl=" in query:
            return base
    return url


_db_url = _url_for_asyncpg(normalize_database_url(DATABASE_URL))
if "+asyncpg" not in _db_url:
    raise RuntimeError(
        "DATABASE_URL deve usar o driver asyncpg, ex.: postgresql+asyncpg://user:pass@host:5432/db "
        "(Supabase: troque postgresql:// por postgresql+asyncpg:// no Render).",
    )

def _db_ssl_enabled() -> bool:
    return os.getenv("DB_SSL", "true").strip().lower() in ("1", "true", "yes", "on")


def _url_requested_ssl(url: str) -> bool:
    if "?" not in url:
        return False
    q = url.partition("?")[2].lower()
    return "sslmode=require" in q or "sslmode=verify-full" in q or "ssl=true" in q


def _is_local_db_host(host: str) -> bool:
    h = host.lower().strip("[]")
    return h in ("localhost", "127.0.0.1", "::1", "postgres", "db")


_host = database_host() or ""
_connect_args: dict = {}
_want_ssl = _db_ssl_enabled() or _url_requested_ssl(DATABASE_URL)
if _host and _want_ssl and not _is_local_db_host(_host):
    # asyncpg: "require" = TLS sem verificar cadeia (Supabase pooler usa cert
    # self-signed na chain; "ssl=True" força verify-full e quebra o handshake).
    # Para verificação completa use DB_SSL_VERIFY=full.
    _verify = os.getenv("DB_SSL_VERIFY", "").strip().lower()
    if _verify in ("full", "verify-full", "verify_full"):
        _connect_args["ssl"] = True
    else:
        _connect_args["ssl"] = "require"

engine = create_async_engine(_db_url, echo=False, connect_args=_connect_args)
SessionLocal = async_sessionmaker[AsyncSession](engine, expire_on_commit=False)
