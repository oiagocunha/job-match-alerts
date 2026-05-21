from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.services import ai as ai_service
from app.services.job_meta import enrich_job_dict


async def upsert_job(session: AsyncSession, data: dict) -> Job:
    stmt = select(Job).where(
        Job.external_id == data["external_id"],
        Job.source == data.get("source", "import"),
    )
    result = await session.execute(stmt)
    job = result.scalar_one_or_none()

    data = enrich_job_dict(data)
    if job is None:
        job = Job(
            external_id=data["external_id"],
            source=data.get("source", "import"),
            title=data["title"],
            company=data.get("company"),
            description=data.get("description") or "",
            location=data.get("location"),
            salary_min=data.get("salary_min"),
            salary_max=data.get("salary_max"),
            url=data.get("url"),
            posted_at=data.get("posted_at"),
            seniority=data.get("seniority"),
            is_remote=data.get("is_remote"),
        )
        session.add(job)
    else:
        job.title = data["title"]
        job.company = data.get("company")
        job.description = data.get("description") or ""
        job.location = data.get("location")
        job.salary_min = data.get("salary_min")
        job.salary_max = data.get("salary_max")
        job.url = data.get("url")
        job.posted_at = data.get("posted_at")
        job.seniority = data.get("seniority")
        job.is_remote = data.get("is_remote")

    await session.commit()
    await session.refresh(job)
    return job


async def list_jobs(session: AsyncSession, limit: int = 50) -> list[Job]:
    stmt = select(Job).order_by(Job.synced_at.desc()).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_job(session: AsyncSession, job_id: int) -> Job | None:
    return await session.get(Job, job_id)


async def delete_job(session: AsyncSession, job_id: int) -> bool:
    job = await session.get(Job, job_id)
    if job is None:
        return False
    await session.delete(job)
    await session.commit()
    return True


async def analyze_job(session: AsyncSession, job: Job) -> Job:
    if not job.description.strip():
        return job
    job.skills_analysis = await ai_service.extract_job_skills(job.description)
    await session.commit()
    await session.refresh(job)
    return job
