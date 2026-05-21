from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate_profile import CandidateProfile
from app.schemas.profile import ProfileStructured, ProfileUpdate

DEMO_USER = "demo"


def _default_label(structured: dict, source_filename: str | None) -> str:
    name = structured.get("name")
    if name and str(name).strip():
        return str(name).strip()[:128]
    if source_filename:
        base = source_filename.rsplit("/", 1)[-1]
        if base.lower().endswith(".pdf"):
            base = base[:-4]
        return base[:128] or "Currículo"
    return "Currículo"


async def list_profiles(
    session: AsyncSession,
    user_id: str = DEMO_USER,
) -> list[CandidateProfile]:
    result = await session.execute(
        select(CandidateProfile)
        .where(CandidateProfile.demo_user_id == user_id)
        .order_by(CandidateProfile.updated_at.desc()),
    )
    return list(result.scalars().all())


async def get_profile_by_id(
    session: AsyncSession,
    profile_id: int,
    user_id: str = DEMO_USER,
) -> CandidateProfile | None:
    result = await session.execute(
        select(CandidateProfile).where(
            CandidateProfile.id == profile_id,
            CandidateProfile.demo_user_id == user_id,
        ),
    )
    return result.scalar_one_or_none()


async def get_profile(
    session: AsyncSession,
    *,
    profile_id: int | None = None,
    user_id: str = DEMO_USER,
) -> CandidateProfile | None:
    if profile_id is not None:
        return await get_profile_by_id(session, profile_id, user_id)
    profiles = await list_profiles(session, user_id)
    return profiles[0] if profiles else None


async def create_profile_from_parse(
    session: AsyncSession,
    *,
    raw_text: str,
    structured: dict,
    source_filename: str | None,
    label: str | None = None,
    user_id: str = DEMO_USER,
) -> CandidateProfile:
    profile = CandidateProfile(
        demo_user_id=user_id,
        label=label or _default_label(structured, source_filename),
        raw_text=raw_text,
        structured=structured,
        source_filename=source_filename,
    )
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile


async def update_profile(
    session: AsyncSession,
    profile_id: int,
    payload: ProfileUpdate,
    user_id: str = DEMO_USER,
) -> CandidateProfile:
    profile = await get_profile_by_id(session, profile_id, user_id)
    if profile is None:
        raise ValueError("Perfil não encontrado.")
    profile.structured = payload.structured.model_dump()
    if payload.raw_text is not None:
        profile.raw_text = payload.raw_text
    if payload.label is not None and payload.label.strip():
        profile.label = payload.label.strip()[:128]
    await session.commit()
    await session.refresh(profile)
    return profile


async def delete_profile(
    session: AsyncSession,
    profile_id: int,
    user_id: str = DEMO_USER,
) -> bool:
    profile = await get_profile_by_id(session, profile_id, user_id)
    if profile is None:
        return False
    await session.delete(profile)
    await session.commit()
    return True


def profile_to_structured(profile: CandidateProfile) -> ProfileStructured:
    return ProfileStructured.model_validate(profile.structured or {})
