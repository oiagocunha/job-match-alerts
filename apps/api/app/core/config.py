import os
import re
from pathlib import Path
from urllib.parse import quote_plus, urlparse

from dotenv import load_dotenv

# Docker: Compose injeta via env_file (não sobrescrever).
# Local: acha a raiz pelo docker-compose.yml e aplica .env + .env.local.
REPO_ROOT: Path | None = None
load_dotenv(override=False)
for _dir in Path(__file__).resolve().parents:
    if (_dir / "docker-compose.yml").is_file():
        REPO_ROOT = _dir
        load_dotenv(_dir / ".env", override=False)
        load_dotenv(_dir / ".env.local", override=True)
        break


def _encode_password_in_url(url: str) -> str:
    """
    Senhas do Supabase costumam ter ?, @, #, etc.
    Se não estiverem percent-encoded, urlparse acha host='postgres'.
    """
    scheme_sep = "://"
    if scheme_sep not in url:
        return url
    scheme, rest = url.split(scheme_sep, 1)
    at_idx = rest.rfind("@")
    if at_idx == -1:
        return url
    creds = rest[:at_idx]
    host_part = rest[at_idx + 1 :]
    colon = creds.find(":")
    if colon == -1:
        return url
    user = creds[:colon]
    password = creds[colon + 1 :]
    if not password or "%" in password:
        return url
    host_only = host_part.split("/")[0].split("?")[0]
    if "." not in host_only.split(":")[0]:
        return url
    if not re.search(r"[?#@/&]", password):
        return url
    return f"{scheme}{scheme_sep}{user}:{quote_plus(password)}@{host_part}"


def normalize_database_url(raw: str) -> str:
    """postgres:// ou postgresql:// → postgresql+asyncpg://; corrige senha sem encode."""
    url = raw.strip().strip('"').strip("'")
    if not url:
        return url
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://") :]
    elif url.startswith("postgresql://") and "+asyncpg" not in url.split("://", 1)[0]:
        url = "postgresql+asyncpg://" + url[len("postgresql://") :]
    return _encode_password_in_url(url)


def build_database_url_from_parts() -> str | None:
    """
    Preferível no Render + Supabase: evita colar URI inteira com senha quebrando o parse.
    Defina DB_HOST, DB_PASSWORD, etc. (deixe DATABASE_URL vazia ou apague).
    """
    host = os.getenv("DB_HOST", "").strip()
    password = os.getenv("DB_PASSWORD", "").strip()
    if not host or not password:
        return None
    user = os.getenv("DB_USER", "postgres").strip() or "postgres"
    port = os.getenv("DB_PORT", "5432").strip() or "5432"
    name = os.getenv("DB_NAME", "postgres").strip() or "postgres"
    safe_pass = quote_plus(password)
    # SSL: asyncpg usa connect_args["ssl"]=True em session.py (não ?sslmode= na URL).
    return f"postgresql+asyncpg://{quote_plus(user)}:{safe_pass}@{host}:{port}/{name}"


def _hostname_of(url: str) -> str | None:
    try:
        return urlparse(url.replace("postgresql+asyncpg", "postgresql")).hostname
    except Exception:
        return None


def _is_managed_hosting() -> bool:
    """Render/Vercel etc. — .env do repo não existe no container."""
    return bool(
        os.getenv("RENDER")
        or os.getenv("RENDER_SERVICE_ID")
        or os.getenv("RENDER_EXTERNAL_URL"),
    )


def _raw_database_url() -> str:
    return os.getenv("DATABASE_URL", "").strip()


def _has_db_parts() -> bool:
    return bool(os.getenv("DB_HOST", "").strip() and os.getenv("DB_PASSWORD", "").strip())


def resolve_database_url() -> str:
    # Regra mais robusta para deploy:
    # - Se DATABASE_URL existir, ela vence (single source of truth).
    # - DB_* vira fallback para evitar mismatch host/user de pooler.
    raw = _raw_database_url()
    if not raw:
        from_parts = build_database_url_from_parts()
        if from_parts:
            return from_parts
        if _is_managed_hosting():
            raise RuntimeError(
                "Banco não configurado no Render. Adicione no painel Environment: "
                "DB_HOST, DB_PASSWORD, DB_USER, DB_PORT, DB_NAME (ou DATABASE_URL encoded). "
                "O .env local não é enviado no deploy.",
            )
        raw = "postgresql+asyncpg://postgres:postgres@localhost:5433/job_match"
    url = normalize_database_url(raw)
    host = _hostname_of(url)

    if host in ("postgres", "db"):
        url = _encode_password_in_url(url)
        host = _hostname_of(url)

    if host == "db":
        raise RuntimeError(
            "DATABASE_URL usa host 'db' (só existe no Docker Compose local). "
            "No Render: apague DATABASE_URL e cadastre DB_HOST, DB_PASSWORD, DB_USER, DB_PORT, DB_NAME "
            "(veja .env na raiz do repo).",
        )
    if host == "postgres":
        raise RuntimeError(
            "DATABASE_URL inválida: senha com ? ou @ quebrou o host (ficou 'postgres'). "
            "No Render prefira DB_HOST=db.xxxx.supabase.co + DB_PASSWORD (senha crua) "
            "OU DATABASE_URL=postgresql+asyncpg://postgres:SENHA_ENCODED@db.xxxx.supabase.co:5432/postgres",
        )
    return url


DATABASE_URL = resolve_database_url()


def database_host() -> str | None:
    return _hostname_of(DATABASE_URL)


def database_url_source() -> str:
    if _raw_database_url():
        return "DATABASE_URL"
    if _has_db_parts():
        return "DB_* parts"
    return "DATABASE_URL"


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380/0")
def _normalize_cors_origin(origin: str) -> str:
    o = origin.strip()
    if len(o) > 1 and o.endswith("/"):
        o = o.rstrip("/")
    return o


CORS_ORIGINS = [
    _normalize_cors_origin(origin)
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
_default_uploads = str(REPO_ROOT / "uploads") if REPO_ROOT else "uploads"
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", _default_uploads))
