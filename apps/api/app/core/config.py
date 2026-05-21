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
    url = _encode_password_in_url(url)
    return url


_raw_db = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5433/job_match",
)
DATABASE_URL = normalize_database_url(_raw_db)


def database_host() -> str | None:
    try:
        parsed = urlparse(DATABASE_URL.replace("postgresql+asyncpg", "postgresql"))
        return parsed.hostname
    except Exception:
        return None
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380/0")
CORS_ORIGINS = [
    origin.strip()
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
