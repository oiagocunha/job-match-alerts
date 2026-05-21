from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.match import MatchBreakdown, MatchJobRequest, MatchRankResponse, MatchResult, RankedJobMatch
from app.services import ai as ai_service
from app.services import profiles as profiles_service
from app.services.ats_engine import compute_match
from app.services import jobs as jobs_service

router = APIRouter(prefix="/match", tags=["ATS Match"])


@router.get("/rank", response_model=MatchRankResponse, summary="Ranking ATS vs vagas salvas")
async def rank_jobs_route(
    session: AsyncSession = Depends(get_session),
    profile_id: int | None = Query(default=None, description="Currículo a usar no score"),
    limit: int = Query(default=20, ge=1, le=50),
    remote_only: bool = Query(default=False),
    seniority: str | None = Query(default=None),
    min_score: float = Query(default=0, ge=0, le=100),
) -> MatchRankResponse:
    profile = await profiles_service.get_profile(session, profile_id=profile_id)
    if profile is None:
        return MatchRankResponse(results=[], profile_required=True)

    structured = profiles_service.profile_to_structured(profile)
    jobs = await jobs_service.list_jobs(session, limit=100)
    ranked: list[RankedJobMatch] = []

    for job in jobs:
        if remote_only and not job.is_remote:
            continue
        if seniority and seniority != "any" and job.seniority != seniority:
            continue

        result = compute_match(
            structured,
            job_title=job.title,
            job_description=job.description,
            skills_analysis=job.skills_analysis,
        )
        if result["score"] < min_score:
            continue
        ranked.append(
            RankedJobMatch(
                job_id=job.id,
                title=job.title,
                company=job.company,
                source=job.source,
                url=job.url,
                is_remote=job.is_remote,
                seniority=job.seniority,
                match=MatchResult(
                    breakdown=MatchBreakdown.model_validate(result["breakdown"]),
                    **{k: v for k, v in result.items() if k != "breakdown"},
                ),
            ),
        )

    ranked.sort(key=lambda item: item.match.score, reverse=True)
    return MatchRankResponse(results=ranked[:limit], profile_required=False)


@router.post(
    "/jobs/{job_id}",
    response_model=MatchResult,
    summary="Score ATS para uma vaga",
)
async def match_single_job_route(
    job_id: int,
    payload: MatchJobRequest,
    session: AsyncSession = Depends(get_session),
    profile_id: int | None = Query(default=None),
) -> MatchResult:
    profile = await profiles_service.get_profile(session, profile_id=profile_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cadastre seu perfil antes (upload de currículo).",
        )

    job = await jobs_service.get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaga não encontrada.")

    if payload.analyze_if_needed and not job.skills_analysis and ai_service.is_configured():
        job.skills_analysis = await ai_service.extract_job_skills(job.description)
        await session.commit()
        await session.refresh(job)

    structured = profiles_service.profile_to_structured(profile)
    result = compute_match(
        structured,
        job_title=job.title,
        job_description=job.description,
        skills_analysis=job.skills_analysis,
    )
    return MatchResult(
        breakdown=MatchBreakdown.model_validate(result["breakdown"]),
        **{k: v for k, v in result.items() if k != "breakdown"},
    )
