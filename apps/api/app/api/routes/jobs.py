from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.job import (
    JobAnalyzeRequest,
    JobAnalyzeResponse,
    JobImportRequest,
    JobImportResponse,
    JobRead,
)
from app.schemas.match import MatchBreakdown, MatchResult
from app.services import ai as ai_service
from app.services import job_import as job_import_service
from app.services import jobs as jobs_service
from app.services import profiles as profiles_service
from app.services.ats_engine import compute_match

router = APIRouter(prefix="/jobs", tags=["Vagas"])


def _openai_http_error(exc: ai_service.OpenAIError) -> HTTPException:
    code = (
        status.HTTP_503_SERVICE_UNAVAILABLE
        if "não configurad" in str(exc).lower()
        else status.HTTP_502_BAD_GATEWAY
    )
    return HTTPException(status_code=code, detail=str(exc))


@router.post(
    "/import",
    response_model=JobImportResponse,
    summary="Cadastrar vaga por URL e calcular score ATS",
)
async def import_job_route(
    payload: JobImportRequest,
    session: AsyncSession = Depends(get_session),
    analyze: bool = Query(default=True, description="Extrair skills da vaga com OpenAI"),
    profile_id: int | None = Query(default=None, description="Currículo para o score ATS"),
) -> JobImportResponse:
    try:
        job_data = await job_import_service.fetch_job_from_url(payload.url)
    except job_import_service.JobImportError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    job = await jobs_service.upsert_job(session, job_data)

    if analyze and ai_service.is_configured() and job.description.strip():
        try:
            job = await jobs_service.analyze_job(session, job)
        except ai_service.OpenAIError as exc:
            raise _openai_http_error(exc) from exc

    profile = await profiles_service.get_profile(session, profile_id=profile_id)
    match_result: MatchResult | None = None
    profile_required = profile is None

    if profile is not None:
        structured = profiles_service.profile_to_structured(profile)
        raw = compute_match(
            structured,
            job_title=job.title,
            job_description=job.description,
            skills_analysis=job.skills_analysis,
        )
        match_result = MatchResult(
            breakdown=MatchBreakdown.model_validate(raw["breakdown"]),
            **{k: v for k, v in raw.items() if k != "breakdown"},
        )

    return JobImportResponse(
        job=JobRead.model_validate(job),
        match=match_result,
        profile_required=profile_required,
    )


@router.get("", response_model=list[JobRead], summary="Listar vagas cadastradas")
async def list_jobs_route(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[JobRead]:
    jobs = await jobs_service.list_jobs(session, limit=limit)
    return [JobRead.model_validate(j) for j in jobs]


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remover vaga")
async def delete_job_route(
    job_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    if not await jobs_service.delete_job(session, job_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaga não encontrada.")


@router.post("/analyze", response_model=JobAnalyzeResponse, summary="Extrair skills de texto")
async def analyze_description_route(payload: JobAnalyzeRequest) -> JobAnalyzeResponse:
    try:
        result = await ai_service.extract_job_skills(payload.description)
    except ai_service.OpenAIError as exc:
        raise _openai_http_error(exc) from exc
    return JobAnalyzeResponse.model_validate(result)


@router.post("/{job_id}/analyze", response_model=JobRead, summary="Reanalisar vaga salva")
async def analyze_saved_job_route(
    job_id: int,
    session: AsyncSession = Depends(get_session),
) -> JobRead:
    job = await jobs_service.get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaga não encontrada.")
    try:
        job = await jobs_service.analyze_job(session, job)
    except ai_service.OpenAIError as exc:
        raise _openai_http_error(exc) from exc
    return JobRead.model_validate(job)
