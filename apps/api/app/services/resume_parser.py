from __future__ import annotations

import re
from io import BytesIO
from typing import Any

from pypdf import PdfReader

SKILL_HINTS = [
    "python",
    "javascript",
    "typescript",
    "react",
    "node",
    "fastapi",
    "django",
    "postgresql",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "git",
    "sql",
    "java",
    "go",
    "rust",
    "n8n",
    "redis",
]

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def extract_text_from_pdf(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


def _guess_skills(text: str) -> list[str]:
    lower = text.lower()
    found: list[str] = []
    for skill in SKILL_HINTS:
        if skill in lower:
            found.append(skill.title() if skill != "n8n" else "n8n")
    # Capitalized tech words
    for match in re.findall(r"\b([A-Z][a-zA-Z+#.]{2,})\b", text):
        if match.lower() not in {s.lower() for s in found} and len(found) < 30:
            if any(c.isupper() for c in match[1:]) or "+" in match:
                found.append(match)
    return sorted(set(found), key=str.lower)[:40]


def _guess_seniority(text: str) -> str:
    from app.services.job_meta import detect_seniority

    return detect_seniority(text, text)


def _guess_name(lines: list[str]) -> str | None:
    for line in lines[:8]:
        clean = line.strip()
        if 3 <= len(clean) <= 60 and "@" not in clean and not clean.lower().startswith("http"):
            if sum(ch.isalpha() for ch in clean) > len(clean) * 0.6:
                return clean
    return None


def parse_resume_text(text: str) -> dict[str, Any]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    email_match = EMAIL_RE.search(text)
    return {
        "name": _guess_name(lines),
        "email": email_match.group(0) if email_match else None,
        "headline": lines[1] if len(lines) > 1 else None,
        "skills": _guess_skills(text),
        "experience_years": {},
        "seniority": _guess_seniority(text),
        "languages": [],
        "education": [],
        "experiences": [],
    }


async def parse_resume_pdf(data: bytes) -> tuple[str, dict[str, Any]]:
    raw = extract_text_from_pdf(data)
    if not raw or len(raw) < 40:
        raise ValueError("Não foi possível extrair texto suficiente do PDF.")
    structured = parse_resume_text(raw)
    return raw, structured
