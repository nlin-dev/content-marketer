from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Claim, claim_sources
from app.schemas import ClaimResponse, ClaimSearchResult, ClaimSourceResponse

router = APIRouter(prefix="/api/claims", tags=["claims"])


async def _build_claim_response(claim: Claim, db: AsyncSession) -> ClaimResponse:
    sources_result = await db.execute(
        select(claim_sources.c.source_id).where(
            claim_sources.c.claim_id == claim.id
        )
    )
    sources = [
        ClaimSourceResponse(source_id=row[0]) for row in sources_result
    ]
    return ClaimResponse(
        id=claim.id,
        text=claim.text,
        category=claim.category,
        sources=sources,
        is_active=claim.is_active,
        created_at=claim.created_at,
    )


@router.post("/discover", response_model=list[ClaimSearchResult])
async def discover_claims(
    q: str,
    db: AsyncSession = Depends(get_db),
) -> list[ClaimSearchResult]:
    from app.services.orchestrator import discover_claims as _discover_claims

    results = await _discover_claims(q, db, limit=10)
    out: list[ClaimSearchResult] = []
    for item in results:
        claim_resp = await _build_claim_response(item["claim"], db)
        out.append(ClaimSearchResult(claim=claim_resp, distance=item["distance"]))
    return out


@router.get("/search", response_model=list[ClaimSearchResult])
async def search_claims(
    q: str,
    db: AsyncSession = Depends(get_db),
) -> list[ClaimSearchResult]:
    from app.services.claim_retrieval import search_claims as _search_claims

    results = await _search_claims(q, db)
    out: list[ClaimSearchResult] = []
    for claim, distance in results:
        claim_resp = await _build_claim_response(claim, db)
        out.append(ClaimSearchResult(claim=claim_resp, distance=distance))
    return out


@router.get("/all", response_model=list[ClaimResponse])
async def get_all_claims(
    db: AsyncSession = Depends(get_db),
) -> list[ClaimResponse]:
    result = await db.execute(select(Claim))
    claims = result.scalars().all()
    out: list[ClaimResponse] = []
    for claim in claims:
        out.append(await _build_claim_response(claim, db))
    return out
