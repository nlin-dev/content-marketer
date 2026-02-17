from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.services.embedding import generate_embedding


async def search_claims(
    query: str, db: AsyncSession, limit: int = 10
) -> list[tuple[Claim, float]]:
    query_embedding = await generate_embedding(query)
    distance = Claim.embedding.cosine_distance(query_embedding).label("distance")
    stmt = (
        select(Claim, distance)
        .where(Claim.is_active == True)  # noqa: E712
        .order_by(distance)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [(row.Claim, row.distance) for row in result]


async def search_claims_by_brief(
    brief_responses: dict,
    project_config: dict,
    db: AsyncSession,
) -> dict[str, list[tuple[Claim, float]]]:
    audience = project_config.get("audience", "")
    goal = project_config.get("goal", "")
    tone = project_config.get("tone", "")
    context_prefix = " ".join(filter(None, [audience, goal, tone]))

    seen_claim_ids: dict[str, tuple[str, float]] = {}
    raw_results: dict[str, list[tuple[Claim, float]]] = {}

    for key, value in brief_responses.items():
        if not isinstance(value, str) or not value.strip():
            continue
        augmented_query = f"{context_prefix}: {value}" if context_prefix else value
        results = await search_claims(augmented_query, db)
        raw_results[key] = results

        for claim, dist in results:
            if claim.id not in seen_claim_ids or dist < seen_claim_ids[claim.id][1]:
                seen_claim_ids[claim.id] = (key, dist)

    deduplicated: dict[str, list[tuple[Claim, float]]] = {}
    for key, results in raw_results.items():
        deduplicated[key] = [
            (claim, dist)
            for claim, dist in results
            if seen_claim_ids[claim.id][0] == key
        ]

    return deduplicated
