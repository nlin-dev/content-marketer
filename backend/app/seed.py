import asyncio
import os
import uuid

from sqlalchemy import text

from app.database import async_session_maker
from app.models import (
    ApprovedAsset,
    AssetType,
    Claim,
    ClaimCategory,
    User,
    UserRole,
    claim_sources,
)
from app.seed_data import ASSETS, CLAIMS


async def truncate_all(session):
    await session.execute(
        text(
            "TRUNCATE claims, claim_sources, approved_assets, users, projects, "
            "content_versions, content_version_claims, content_version_assets, "
            "compliance_records, comments, audit_logs CASCADE"
        )
    )


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("WARNING: OPENAI_API_KEY not set, using zero vectors for embeddings")
        return [[0.0] * 1536 for _ in texts]

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    response = await client.embeddings.create(
        model="text-embedding-3-small", input=texts
    )
    return [item.embedding for item in response.data]


async def seed_claims(session, embeddings: list[list[float]]):
    for i, claim_data in enumerate(CLAIMS):
        claim = Claim(
            id=claim_data["id"],
            text=claim_data["text"],
            category=ClaimCategory(claim_data["category"]),
            embedding=embeddings[i],
        )
        session.add(claim)

    await session.flush()

    rows = []
    for claim_data in CLAIMS:
        for source in claim_data["sources"]:
            rows.append({"claim_id": claim_data["id"], "source_id": source})
    if rows:
        await session.execute(claim_sources.insert().values(rows))


async def seed_assets(session):
    for asset_data in ASSETS:
        session.add(ApprovedAsset(
            id=asset_data["id"],
            name=asset_data["name"],
            asset_type=AssetType(asset_data["asset_type"]),
            file_url=asset_data["file_url"],
            metadata_=asset_data["metadata"],
        ))


async def seed():
    texts = [c["text"] for c in CLAIMS]
    embeddings = await generate_embeddings(texts)

    async with async_session_maker() as session:
        async with session.begin():
            await truncate_all(session)

            session.add(User(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, "user-dev")),
                email="dev@example.com",
                display_name="Dev User",
                role=UserRole.EDITOR,
            ))

            await seed_claims(session, embeddings)
            await seed_assets(session)

    print(f"Seeded: 1 user, {len(CLAIMS)} claims, {len(ASSETS)} assets")


if __name__ == "__main__":
    asyncio.run(seed())
