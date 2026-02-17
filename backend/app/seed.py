import asyncio
import logging
import uuid
from pathlib import Path

from sqlalchemy import text

from app.config import settings
from app.database import async_session_maker
from app.ingestion.pipeline import run_pipeline
from app.models import (
    ApprovedAsset,
    AssetType,
    Claim,
    ClaimCategory,
    User,
    UserRole,
    claim_sources,
)

logger = logging.getLogger(__name__)

PDF_DIR = Path(__file__).resolve().parent.parent / "fixtures"
VISUAL_AID = PDF_DIR / "visual-aid.pdf"
PRESCRIPTION = PDF_DIR / "medication-prescription.pdf"


async def truncate_all(session):
    await session.execute(
        text(
            "TRUNCATE claims, claim_sources, approved_assets, users, projects, "
            "content_versions, content_version_claims, content_version_assets, "
            "compliance_records, comments, audit_logs CASCADE"
        )
    )


async def seed():
    pdf_paths = [p for p in [VISUAL_AID, PRESCRIPTION] if p.exists()]
    if not pdf_paths:
        print("ERROR: No PDF files found in fixtures/. Cannot seed.")
        return

    print(f"Ingesting {len(pdf_paths)} PDFs...")
    result = await run_pipeline(
        pdf_paths,
        anthropic_api_key=settings.anthropic_api_key,
        openai_api_key=settings.openai_api_key,
        model=settings.anthropic_model,
    )

    async with async_session_maker() as session:
        async with session.begin():
            await truncate_all(session)

            # Default dev user
            session.add(User(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, "user-dev")),
                email="dev@example.com",
                display_name="Dev User",
                role=UserRole.EDITOR,
            ))

            # Insert claims with embeddings
            for i, claim in enumerate(result.claims):
                claim_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"claim-{claim.text[:50]}"))
                embedding = result.embeddings[i] if i < len(result.embeddings) else None
                if embedding is None:
                    logger.warning("No embedding for claim %d: %s", i, claim.text[:60])
                db_claim = Claim(
                    id=claim_id,
                    text=claim.text,
                    category=ClaimCategory(claim.category),
                    confidence=claim.confidence,
                    embedding=embedding,
                )
                session.add(db_claim)

                # Link source reference
                await session.execute(
                    claim_sources.insert().values(
                        claim_id=claim_id, source_id=claim.source_ref
                    )
                )

            # Insert assets
            for asset in result.assets:
                asset_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"asset-{asset.slug}"))
                session.add(ApprovedAsset(
                    id=asset_id,
                    name=asset.name,
                    asset_type=AssetType(asset.asset_type),
                    file_url=f"/static/assets/{asset.slug}.svg",
                    metadata_={
                        "description": asset.name,
                        "source_pdf": asset.filename,
                        "source_page": asset.source_page,
                    },
                ))

            # Insert ISI as a document asset
            if result.isi_html:
                isi_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "asset-isi-block"))
                session.add(ApprovedAsset(
                    id=isi_id,
                    name="ISI Block",
                    asset_type=AssetType.DOCUMENT,
                    file_url="/static/assets/isi-block.html",
                    metadata_={"html": result.isi_html},
                ))

    coverage_info = ""
    if result.coverage:
        coverage_info = f", coverage={result.coverage.coverage_ratio:.1%}"
    print(
        f"Seeded: 1 user, {len(result.claims)} claims, "
        f"{len(result.assets)} assets, ISI={'yes' if result.isi_html else 'no'}{coverage_info}"
    )


if __name__ == "__main__":
    asyncio.run(seed())
