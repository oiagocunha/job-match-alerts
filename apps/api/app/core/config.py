import os
from pathlib import Path

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

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5433/job_match",
)
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
