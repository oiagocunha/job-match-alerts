from app.schemas.profile import ProfileStructured
from app.services.ats_engine import _skill_overlap, compute_match


def test_skill_overlap_uses_each_required_skill() -> None:
    score, matched, missing = _skill_overlap(
        ["Python", "FastAPI", "Docker"],
        ["Python", "Kafka"],
        [],
    )
    assert "Python" in matched
    assert "Kafka" in missing
    assert score > 0


def test_compute_match_returns_breakdown_keys() -> None:
    profile = ProfileStructured(
        skills=["Python", "FastAPI", "Kafka"],
        seniority="senior",
    )
    result = compute_match(
        profile,
        job_title="Backend Senior Python",
        job_description="Precisamos de Python, FastAPI e experiência com APIs.",
        skills_analysis={
            "skills_required": ["Python", "FastAPI"],
            "skills_nice_to_have": ["Kafka"],
            "seniority": "senior",
        },
    )
    assert "semantic_match" in result["breakdown"]
    assert 0 <= result["score"] <= 100
