from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from app.ingestion.asset_extractor import ExtractedAsset, extract_assets
from app.ingestion.claim_extractor import ExtractedClaim, extract_claims
from app.ingestion.isi_extractor import extract_isi_html
from app.ingestion.pdf_parser import PageContent, extract_pages, extract_sections, is_image_only
from app.services.embedding import batch_generate_embeddings

logger = logging.getLogger(__name__)

EMBEDDING_BATCH_SIZE = 100


@dataclass
class IngestionResult:
    claims: list[ExtractedClaim] = field(default_factory=list)
    assets: list[ExtractedAsset] = field(default_factory=list)
    isi_html: str | None = None
    embeddings: list[list[float]] = field(default_factory=list)



def classify_pdf(pdf_path: Path, pages: list[PageContent] | None = None) -> str:
    if pages is None:
        pages = extract_pages(pdf_path)
    sample = " ".join(p.text for p in pages[:3]).upper()
    pi_markers = ["INDICATIONS AND USAGE", "DOSAGE AND ADMINISTRATION", "PRESCRIBING INFORMATION"]
    if any(marker in sample for marker in pi_markers):
        return "prescribing_info"
    return "visual_aid"


async def run_pipeline(
    pdf_paths: list[Path],
    *,
    anthropic_api_key: str,
    openai_api_key: str,
    model: str = "claude-sonnet-4-20250514",
) -> IngestionResult:
    all_claims: list[ExtractedClaim] = []
    all_assets: list[ExtractedAsset] = []
    isi_html: str | None = None

    for pdf_path in pdf_paths:
        pages = extract_pages(pdf_path)
        pdf_type = classify_pdf(pdf_path, pages)
        filename = pdf_path.name

        mode = "vision" if is_image_only(pages) else "text"
        logger.info("Processing %s as %s via %s (%d pages)", filename, pdf_type, mode, len(pages))

        # Extract claims from all PDFs
        claims = await extract_claims(pages, filename, api_key=anthropic_api_key, model=model, pdf_path=pdf_path)
        all_claims.extend(claims)

        if pdf_type == "visual_aid":
            assets = await extract_assets(pages, filename, api_key=anthropic_api_key, model=model, pdf_path=pdf_path)
            all_assets.extend(assets)

        elif pdf_type == "prescribing_info":
            sections = extract_sections(pdf_path)
            isi_html = await extract_isi_html(sections, api_key=anthropic_api_key, model=model)

    # Deduplicate claims by normalized text
    all_claims = _deduplicate_claims(all_claims)

    # Generate embeddings in batches
    embeddings: list[list[float]] = []
    claim_texts = [c.text for c in all_claims]
    for i in range(0, len(claim_texts), EMBEDDING_BATCH_SIZE):
        batch = claim_texts[i : i + EMBEDDING_BATCH_SIZE]
        batch_embeddings = await batch_generate_embeddings(batch)
        embeddings.extend(batch_embeddings)

    logger.info(
        "Pipeline complete: %d claims, %d assets, ISI=%s",
        len(all_claims),
        len(all_assets),
        "yes" if isi_html else "no",
    )

    return IngestionResult(
        claims=all_claims,
        assets=all_assets,
        isi_html=isi_html,
        embeddings=embeddings,
    )


def _deduplicate_claims(claims: list[ExtractedClaim]) -> list[ExtractedClaim]:
    seen: dict[str, ExtractedClaim] = {}
    for claim in claims:
        key = claim.text.strip().lower()
        if key not in seen:
            seen[key] = claim
    return list(seen.values())
