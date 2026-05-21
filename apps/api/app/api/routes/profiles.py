from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.config import UPLOAD_DIR
from app.schemas.profile import ProfileRead, ProfileStructured, ProfileSummary, ProfileUpdate
from app.services import ai as ai_service
from app.services import profiles as profiles_service
from app.services.resume_parser import parse_resume_pdf

router = APIRouter(prefix="/profiles", tags=["Perfil"])


def _to_read(profile) -> ProfileRead:
    return ProfileRead(
        id=profile.id,
        demo_user_id=profile.demo_user_id,
        label=profile.label,
        raw_text=profile.raw_text,
        structured=ProfileStructured.model_validate(profile.structured),
        source_filename=profile.source_filename,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def _to_summary(profile) -> ProfileSummary:
    structured = ProfileStructured.model_validate(profile.structured or {})
    return ProfileSummary(
        id=profile.id,
        label=profile.label,
        name=structured.name,
        headline=structured.headline,
        skills_count=len(structured.skills),
        seniority=structured.seniority,
        source_filename=profile.source_filename,
        updated_at=profile.updated_at,
    )


@router.get("", response_model=list[ProfileSummary], summary="Listar currículos salvos")
async def list_profiles_route(
    session: AsyncSession = Depends(get_session),
) -> list[ProfileSummary]:
    profiles = await profiles_service.list_profiles(session)
    return [_to_summary(p) for p in profiles]


@router.get("/me", response_model=ProfileRead, summary="Perfil mais recente (legado)")
async def get_my_profile_route(
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    profile = await profiles_service.get_profile(session)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado.")
    return _to_read(profile)


@router.get("/{profile_id}", response_model=ProfileRead, summary="Obter currículo por id")
async def get_profile_route(
    profile_id: int,
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    profile = await profiles_service.get_profile_by_id(session, profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado.")
    return _to_read(profile)


@router.post(
    "/parse",
    response_model=ProfileRead,
    summary="Upload PDF  cria novo currículo salvo",
)
async def parse_resume_route(
    file: UploadFile = File(...),
    use_ai: bool = True,
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Envie um arquivo PDF.",
        )

    data = await file.read()
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PDF muito grande (máx. 8MB).")

    try:
        raw_text, structured = await parse_resume_pdf(data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if use_ai and ai_service.is_configured():
        try:
            enhanced = await ai_service.parse_resume_structured(raw_text)
            structured = {**structured, **enhanced}
        except ai_service.OpenAIError:
            structured["parse_note"] = "OpenAI indisponível; campos gerados por heurística."

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = file.filename.replace("..", "").replace("/", "_")
    (UPLOAD_DIR / "demo").mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / "demo" / safe_name
    dest.write_bytes(data)

    try:
        profile = await profiles_service.create_profile_from_parse(
            session,
            raw_text=raw_text,
            structured=structured,
            source_filename=safe_name,
        )
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível criar outro currículo (banco ainda com limite de um perfil). Reinicie a API para aplicar migrações.",
        ) from exc
    return _to_read(profile)


@router.put("/{profile_id}", response_model=ProfileRead, summary="Atualizar currículo")
async def update_profile_route(
    profile_id: int,
    payload: ProfileUpdate,
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    try:
        profile = await profiles_service.update_profile(session, profile_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_read(profile)


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir currículo")
async def delete_profile_route(
    profile_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    if not await profiles_service.delete_profile(session, profile_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado.")
