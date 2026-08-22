"""Работа России: live open-data feed, filtered for self-employment/NPD/contract work."""

import asyncio
from typing import Optional

import httpx
from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/jobs", tags=["jobs"])
# The official open-data documentation currently describes this API over HTTP.
TRUDVSEM_API = "http://opendata.trudvsem.ru/api/v1/vacancies"
SEARCH_TERMS = ("самозанят", "нпд", "налог на профессиональный доход", "гпх", "гражданско-правов")


def _is_self_employed(v: dict) -> bool:
    text = " ".join(str(v.get(k, "")) for k in ("job-name", "duty", "employment", "vacancy", "category")).lower()
    return any(term in text for term in SEARCH_TERMS)


def _normalize(item: dict) -> Optional[dict]:
    v = item.get("vacancy", item)
    if not isinstance(v, dict) or not _is_self_employed(v):
        return None
    return {
        "id": str(v.get("id", "")),
        "title": v.get("job-name") or v.get("title") or "Предложение",
        "company": (v.get("company") or {}).get("name") if isinstance(v.get("company"), dict) else v.get("company", ""),
        "region": (v.get("region") or {}).get("name") if isinstance(v.get("region"), dict) else v.get("region", ""),
        "salary": v.get("salary") or "",
        "salary_min": v.get("salary_min"),
        "salary_max": v.get("salary_max"),
        "employment": v.get("employment") or "",
        "schedule": v.get("schedule") or "",
        "duty": v.get("duty") or "",
        "url": v.get("vac_url") or "https://trudvsem.ru/",
        "created_at": v.get("creation-date") or "",
        "source": "Работа России / trudvsem.ru",
    }


@router.get("/self-employed")
async def self_employed_jobs(
    q: str = Query("самозанятый", min_length=2, max_length=120),
    region: Optional[str] = Query(None, max_length=120),
    limit: int = Query(20, ge=1, le=50),
):
    """Public live feed from the official open-data portal; no user account is required."""
    queries = [q, "самозанятый", "НПД", "ГПХ"]
    if region:
        queries = [f"{x} {region}" for x in queries]

    async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
        async def fetch(text: str):
            r = await client.get(TRUDVSEM_API, params={"text": text, "limit": 100, "offset": 0}, headers={"Accept": "application/json"})
            r.raise_for_status()
            return r.json()
        results = await asyncio.gather(*(fetch(x) for x in queries), return_exceptions=True)

    seen = set()
    items = []
    for data in results:
        if isinstance(data, Exception):
            continue
        for raw in ((data.get("results") or {}).get("vacancies") or []):
            item = _normalize(raw)
            if item and item["id"] not in seen:
                seen.add(item["id"])
                items.append(item)
                if len(items) >= limit:
                    break
        if len(items) >= limit:
            break
    return {"items": items, "count": len(items), "source": "trudvsem.ru", "filter": "явно указана самозанятость / НПД / ГПХ"}
