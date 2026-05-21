from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.core.config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"

SKILLS_PROMPT = """Você extrai requisitos de vagas de emprego em TI.
Analise a descrição e retorne APENAS JSON válido com este formato:
{
  "skills_required": ["skill1", "skill2"],
  "skills_nice_to_have": ["skill3"],
  "seniority": "junior|mid|senior|lead|unknown",
  "summary": "uma frase em português"
}
Use termos curtos e padronizados (ex.: Python, FastAPI, React).
Se não houver informação, use listas vazias e seniority "unknown"."""

RESUME_PROMPT = """Você extrai dados estruturados de currículos de TI em português ou inglês.
Retorne APENAS JSON válido:
{
  "name": "string|null",
  "email": "string|null",
  "headline": "string|null",
  "skills": ["Python", "React"],
  "experience_years": {"python": 4, "react": 3},
  "seniority": "junior|mid|senior|lead|unknown",
  "languages": ["pt-BR"],
  "education": ["Bacharelado em ..."],
  "experiences": [{"title": "...", "company": "...", "period": "2020-2024"}]
}"""


class OpenAIError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def is_configured() -> bool:
    return bool(OPENAI_API_KEY)


async def extract_job_skills(description: str) -> dict[str, Any]:
    if not is_configured():
        raise OpenAIError("OPENAI_API_KEY não configurada.")

    text = description.strip()
    if not text:
        raise OpenAIError("Descrição da vaga vazia.")

    if len(text) > 12_000:
        text = text[:12_000] + "\n...[truncado]"

    payload = {
        "model": OPENAI_MODEL,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SKILLS_PROMPT},
            {"role": "user", "content": text},
        ],
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            OPENAI_CHAT_URL,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    if response.status_code >= 400:
        logger.warning("OpenAI HTTP %s: %s", response.status_code, response.text[:300])
        raise OpenAIError(
            f"OpenAI retornou HTTP {response.status_code}.",
            status_code=response.status_code,
        )

    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        raise OpenAIError("Resposta da OpenAI em formato inesperado.") from exc

    return {
        "skills_required": parsed.get("skills_required") or [],
        "skills_nice_to_have": parsed.get("skills_nice_to_have") or [],
        "seniority": parsed.get("seniority") or "unknown",
        "summary": parsed.get("summary") or "",
        "model": OPENAI_MODEL,
    }


async def parse_resume_structured(raw_text: str) -> dict[str, Any]:
    if not is_configured():
        raise OpenAIError("OPENAI_API_KEY não configurada.")
    text = raw_text.strip()[:14_000]
    payload = {
        "model": OPENAI_MODEL,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": RESUME_PROMPT},
            {"role": "user", "content": text},
        ],
    }
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            OPENAI_CHAT_URL,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
    if response.status_code >= 400:
        logger.warning("OpenAI HTTP %s: %s", response.status_code, response.text[:300])
        raise OpenAIError(
            f"OpenAI retornou HTTP {response.status_code}.",
            status_code=response.status_code,
        )

    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        raise OpenAIError("Resposta da OpenAI em formato inesperado.") from exc


async def ping() -> str:
    """Valida a chave sem gastar tokens de chat."""
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        )
    if response.status_code >= 400:
        raise OpenAIError(
            f"OpenAI retornou HTTP {response.status_code}.",
            status_code=response.status_code,
        )
    return "API acessível"
