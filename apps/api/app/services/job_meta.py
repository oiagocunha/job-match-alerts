from __future__ import annotations

import re
from typing import Any

REMOTE_PATTERNS = re.compile(
    r"\b(remoto|remote|home\s*office|work\s*from\s*home|wfh|teletrabalho|"
    r"anywhere|híbrido|hibrido|hybrid)\b",
    re.IGNORECASE,
)

SENIORITY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("intern", re.compile(r"\b(est[aá]gio|estagi[aá]rio|intern)\b", re.I)),
    ("junior", re.compile(r"\b(j[uú]nior|jr\.?|entry)\b", re.I)),
    ("mid", re.compile(r"\b(pleno|mid|intermedi[aá]rio)\b", re.I)),
    ("senior", re.compile(r"\b(s[eê]nior|sr\.?)\b", re.I)),
    ("lead", re.compile(r"\b(lead|staff|principal|coordenador|gerente)\b", re.I)),
]

SENIORITY_RANK = {"intern": 0, "junior": 1, "mid": 2, "senior": 3, "lead": 4, "unknown": 2}


def detect_remote(title: str, description: str, location: str | None) -> bool:
    blob = f"{title}\n{description}\n{location or ''}"
    return bool(REMOTE_PATTERNS.search(blob))


def detect_seniority(title: str, description: str = "") -> str:
    blob = f"{title}\n{description[:1500]}"
    found: list[str] = []
    for label, pattern in SENIORITY_PATTERNS:
        if pattern.search(blob):
            found.append(label)
    if not found:
        return "unknown"
    return max(found, key=lambda s: SENIORITY_RANK.get(s, 2))


def enrich_job_dict(job: dict[str, Any]) -> dict[str, Any]:
    title = job.get("title") or ""
    description = job.get("description") or ""
    location = job.get("location")
    analysis = job.get("skills_analysis") or {}
    seniority = analysis.get("seniority") if isinstance(analysis, dict) else None
    if not seniority or seniority == "unknown":
        seniority = detect_seniority(title, description)
    job["seniority"] = seniority
    job["is_remote"] = detect_remote(title, description, location)
    return job


def seniority_matches(candidate: str, job: str, *, flexible: bool = True) -> bool:
    c_rank = SENIORITY_RANK.get(candidate, 2)
    j_rank = SENIORITY_RANK.get(job, 2)
    if flexible:
        return c_rank >= j_rank - 1
    return c_rank == j_rank


def filter_jobs(
    jobs: list[dict[str, Any]],
    *,
    remote_only: bool = False,
    seniority: str | None = None,
) -> list[dict[str, Any]]:
    enriched = [enrich_job_dict(dict(j)) for j in jobs]
    if remote_only:
        enriched = [j for j in enriched if j.get("is_remote")]
    if seniority and seniority != "any":
        enriched = [j for j in enriched if j.get("seniority") == seniority]
    return enriched
