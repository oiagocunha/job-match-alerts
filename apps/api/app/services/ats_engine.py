from __future__ import annotations

import re
from typing import Any

from app.schemas.profile import ProfileStructured
from app.services.job_meta import SENIORITY_RANK, seniority_matches

WEIGHTS = {
    "skills": 0.35,
    "seniority": 0.20,
    "experience": 0.25,
    "semantic_match": 0.20,
}


def _normalize_skill(skill: str) -> str:
    return re.sub(r"[^a-z0-9+#.]", "", skill.lower())


def _skill_matches_candidate(norm: str, cand: set[str]) -> bool:
    if not norm:
        return False
    return norm in cand or any(norm in c or c in norm for c in cand)


def _skill_overlap(
    candidate_skills: list[str],
    required: list[str],
    nice: list[str],
) -> tuple[float, list[str], list[str]]:
    cand = {_normalize_skill(s) for s in candidate_skills}
    req_norm = [_normalize_skill(s) for s in required]
    nice_norm = [_normalize_skill(s) for s in nice]

    matched: list[str] = []
    missing: list[str] = []

    for raw, norm in zip(required, req_norm, strict=False):
        if not norm:
            continue
        if _skill_matches_candidate(norm, cand):
            matched.append(raw)
        else:
            missing.append(raw)

    for raw, norm in zip(nice, nice_norm, strict=False):
        if not norm:
            continue
        if _skill_matches_candidate(norm, cand) and raw not in matched:
            matched.append(raw)

    req_total = max(len([n for n in req_norm if n]), 1)
    req_hits = sum(1 for n in req_norm if n and _skill_matches_candidate(n, cand))
    req_score = req_hits / req_total
    nice_bonus = min(0.25, 0.05 * len(nice_norm))
    score = min(100.0, (req_score + nice_bonus) * 100)
    return score, matched, missing


def _seniority_score(candidate: str, job: str) -> float:
    if job == "unknown" or candidate == "unknown":
        return 70.0
    if seniority_matches(candidate, job):
        c_rank = SENIORITY_RANK.get(candidate, 2)
        j_rank = SENIORITY_RANK.get(job, 2)
        if c_rank >= j_rank:
            return 95.0
        return 65.0
    return 35.0


def _experience_score(profile: ProfileStructured, required: list[str]) -> float:
    years_map = profile.experience_years or {}
    if years_map:
        vals = list(years_map.values())
        avg = sum(vals) / len(vals)
        return min(100.0, 50.0 + avg * 12)

    # Heurística: quantidade de skills em comum como proxy
    overlap, _, _ = _skill_overlap(profile.skills, required, [])
    return min(100.0, overlap * 0.85 + 15)


def _semantic_score(profile: ProfileStructured, description: str, required: list[str]) -> float:
    if not description:
        return 50.0
    desc = _normalize_skill(description[:8000])
    hits = 0
    for skill in profile.skills:
        norm = _normalize_skill(skill)
        if norm and norm in desc:
            hits += 1
    for skill in required:
        norm = _normalize_skill(skill)
        if norm and norm in desc:
            hits += 1
    denom = max(len(profile.skills) + len(required), 1)
    return min(100.0, (hits / denom) * 100 * 2.5)


def compute_match(
    profile: ProfileStructured,
    *,
    job_title: str,
    job_description: str,
    skills_analysis: dict[str, Any] | None,
) -> dict[str, Any]:
    analysis = skills_analysis or {}
    required = list(analysis.get("skills_required") or [])
    nice = list(analysis.get("skills_nice_to_have") or [])
    job_seniority = analysis.get("seniority") or "unknown"

    from app.services.job_meta import detect_seniority

    if job_seniority == "unknown":
        job_seniority = detect_seniority(job_title, job_description)

    skills_score, matched, missing = _skill_overlap(profile.skills, required, nice)
    seniority_score = _seniority_score(profile.seniority, job_seniority)
    experience_score = _experience_score(profile, required)
    semantic_score = _semantic_score(profile, job_description, required)

    breakdown = {
        "skills": round(skills_score, 1),
        "seniority": round(seniority_score, 1),
        "experience": round(experience_score, 1),
        "semantic_match": round(semantic_score, 1),
    }
    total = sum(breakdown[k] * WEIGHTS[k] for k in WEIGHTS)
    reasons = []
    if matched:
        reasons.append(f"Skills alinhadas: {', '.join(matched[:8])}")
    if missing:
        reasons.append(f"Skills em falta: {', '.join(missing[:8])}")
    reasons.append(f"Senioridade vaga: {job_seniority} · seu perfil: {profile.seniority}")

    return {
        "score": round(total, 1),
        "breakdown": breakdown,
        "matched": matched,
        "missing": missing,
        "job_seniority": job_seniority,
        "candidate_seniority": profile.seniority,
        "explanation": reasons,
    }
