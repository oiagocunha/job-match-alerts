from __future__ import annotations

import hashlib
import json
import re
from typing import Any
from urllib.parse import urlparse

import httpx

from app.services.job_meta import enrich_job_dict

USER_AGENT = "JobMatchAlerts/0.1 (+portfolio)"


class JobImportError(Exception):
    pass


def detect_source(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "linkedin.com" in host:
        return "linkedin"
    if "gupy.io" in host:
        return "gupy"
    if "inhire.app" in host or "inhire.com" in host:
        return "inhire"
    return "external"


def _strip_html(html: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.I | re.S)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_next_data(html: str) -> dict[str, Any] | None:
    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def _parse_json_ld(html: str) -> dict[str, Any] | None:
    for block in re.findall(
        r'<script type="application/ld\+json">(.*?)</script>',
        html,
        re.S | re.I,
    ):
        try:
            data = json.loads(block)
            if isinstance(data, dict) and data.get("@type") in ("JobPosting", "jobPosting"):
                return data
        except json.JSONDecodeError:
            continue
    return None


async def fetch_job_from_url(url: str) -> dict[str, Any]:
    parsed = urlparse(url)
    if not parsed.scheme.startswith("http"):
        raise JobImportError("URL inválida.")

    source = detect_source(url)
    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "pt-BR,pt;q=0.9"},
    ) as client:
        response = await client.get(url)
    if response.status_code >= 400:
        raise JobImportError(f"Não foi possível acessar a URL (HTTP {response.status_code}).")

    html = response.text
    title = None
    description = ""
    company = None
    location = None

    ld = _parse_json_ld(html)
    if ld:
        title = ld.get("title")
        description = ld.get("description") or ""
        org = ld.get("hiringOrganization") or {}
        if isinstance(org, dict):
            company = org.get("name")
        loc = ld.get("jobLocation") or {}
        if isinstance(loc, dict):
            address = loc.get("address") or {}
            if isinstance(address, dict):
                location = address.get("addressLocality") or address.get("addressRegion")

    og_title = re.search(r'property="og:title" content="([^"]+)"', html, re.I)
    og_desc = re.search(r'property="og:description" content="([^"]+)"', html, re.I)
    if og_title and not title:
        title = og_title.group(1)
    if og_desc and not description:
        description = og_desc.group(1)

    next_data = _extract_next_data(html)
    if next_data and not description:
        blob = json.dumps(next_data, ensure_ascii=False)
        if "description" in blob.lower():
            description = _strip_html(blob)[:12000]

    if not description:
        description = _strip_html(html)[:12000]

    if not title:
        title_match = re.search(r"<title>([^<]+)</title>", html, re.I)
        title = title_match.group(1).strip() if title_match else "Vaga importada"

    for prefix in ("Página da Vaga | ", "P\u00e1gina da Vaga | ", "Job Opening | "):
        if title.startswith(prefix):
            title = title[len(prefix) :].strip()

    external_id = hashlib.sha256(url.encode()).hexdigest()[:16]

    job = {
        "external_id": external_id,
        "title": title,
        "company": company,
        "description": description,
        "location": location,
        "salary_min": None,
        "salary_max": None,
        "url": str(response.url),
        "source": source,
        "posted_at": None,
    }
    return enrich_job_dict(job)
