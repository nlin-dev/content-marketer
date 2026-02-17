from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

from app.ingestion.asset_extractor import ExtractedAsset, extract_assets
from app.ingestion.claim_extractor import ExtractedClaim, extract_claims
from app.ingestion.isi_extractor import extract_isi_html
from app.ingestion.pdf_parser import PageContent, extract_pages, extract_sections, is_image_only
from app.services.embedding import batch_generate_embeddings

logger = logging.getLogger(__name__)

EMBEDDING_BATCH_SIZE = 100

_SIGNAL_TOKEN_PATTERNS = [
    re.compile(r"\d+(?:\.\d+)?%"),                          # percentages
    re.compile(r"HR\s*=\s*\d+\.\d+", re.IGNORECASE),        # hazard ratios
    re.compile(r"p\s*[<>=]\s*\d+\.\d+", re.IGNORECASE),     # p-values
    re.compile(r"\d+(?:\.\d+)?\s+months?", re.IGNORECASE),  # time measurements
    re.compile(r"\d+(?:\.\d+)?\s*mg", re.IGNORECASE),       # dosing
]


@dataclass
class CoverageReport:
    total_tokens: int
    covered_tokens: int
    uncovered_tokens: set[str]
    coverage_ratio: float


@dataclass
class IngestionResult:
    claims: list[ExtractedClaim] = field(default_factory=list)
    assets: list[ExtractedAsset] = field(default_factory=list)
    isi_html: str | None = None
    embeddings: list[list[float]] = field(default_factory=list)
    coverage: CoverageReport | None = None


def extract_signal_tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for pattern in _SIGNAL_TOKEN_PATTERNS:
        for match in pattern.finditer(text):
            tokens.add(match.group(0))
    return tokens


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def deduplicate_claims_with_embeddings(
    claims: list[ExtractedClaim],
    embeddings: list[list[float]],
    threshold: float = 0.95,
) -> list[ExtractedClaim]:
    if not claims:
        return []

    # Sort by confidence descending (greedy: keep highest confidence first)
    indexed = sorted(enumerate(claims), key=lambda x: x[1].confidence, reverse=True)

    # Fast path: exact text dedup
    seen_text: set[str] = set()
    kept_indices: list[int] = []

    for orig_idx, claim in indexed:
        key = claim.text.strip().lower()
        if key in seen_text:
            continue

        # Check cosine similarity against all kept claims
        is_dup = False
        for kept_idx in kept_indices:
            sim = _cosine_similarity(embeddings[orig_idx], embeddings[kept_idx])
            if sim >= threshold:
                is_dup = True
                break

        if not is_dup:
            kept_indices.append(orig_idx)
            seen_text.add(key)

    # Return in original order
    kept_indices.sort()
    return [claims[i] for i in kept_indices]


def _compute_coverage(source_texts: list[str], claims: list[ExtractedClaim]) -> CoverageReport:
    combined_source = " ".join(source_texts)
    combined_claims = " ".join(c.text for c in claims)

    tokens = extract_signal_tokens(combined_source)
    if not tokens:
        return CoverageReport(total_tokens=0, covered_tokens=0, uncovered_tokens=set(), coverage_ratio=1.0)

    covered = {t for t in tokens if t in combined_claims}
    uncovered = tokens - covered

    return CoverageReport(
        total_tokens=len(tokens),
        covered_tokens=len(covered),
        uncovered_tokens=uncovered,
        coverage_ratio=len(covered) / len(tokens) if tokens else 1.0,
    )


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
    all_source_texts: list[str] = []
    isi_html: str | None = None

    for pdf_path in pdf_paths:
        pages = extract_pages(pdf_path)
        pdf_type = classify_pdf(pdf_path, pages)
        filename = pdf_path.name

        mode = "vision" if is_image_only(pages) else "text"
        logger.info("Processing %s as %s via %s (%d pages)", filename, pdf_type, mode, len(pages))

        all_source_texts.extend(p.text for p in pages)

        claims = await extract_claims(pages, filename, api_key=anthropic_api_key, model=model, pdf_path=pdf_path)
        all_claims.extend(claims)

        if pdf_type == "visual_aid":
            assets = await extract_assets(pages, filename, api_key=anthropic_api_key, model=model, pdf_path=pdf_path)
            all_assets.extend(assets)

        elif pdf_type == "prescribing_info":
            sections = extract_sections(pdf_path)
            isi_html = await extract_isi_html(sections, api_key=anthropic_api_key, model=model)

    # Generate embeddings BEFORE dedup (needed for fuzzy matching)
    embeddings: list[list[float]] = []
    claim_texts = [c.text for c in all_claims]
    for i in range(0, len(claim_texts), EMBEDDING_BATCH_SIZE):
        batch = claim_texts[i : i + EMBEDDING_BATCH_SIZE]
        batch_embeddings = await batch_generate_embeddings(batch)
        embeddings.extend(batch_embeddings)

    # Fuzzy deduplication using embeddings
    pre_dedup_count = len(all_claims)
    all_claims = deduplicate_claims_with_embeddings(all_claims, embeddings)
    # Re-index embeddings to match deduplicated claims
    deduped_texts = {c.text for c in all_claims}
    embeddings = [emb for claim, emb in zip(claim_texts, embeddings) if claim in {c.text for c in all_claims}]
    # Rebuild proper embedding list matching deduped order
    text_to_emb = dict(zip(claim_texts, [emb for emb in embeddings] if embeddings else []))
    embeddings = []
    for c in all_claims:
        if c.text in text_to_emb:
            embeddings.append(text_to_emb[c.text])

    # Coverage verification
    coverage = _compute_coverage(all_source_texts, all_claims)

    logger.info(
        "Pipeline complete: %d claims (%d before dedup), %d assets, ISI=%s, coverage=%.1f%%",
        len(all_claims),
        pre_dedup_count,
        len(all_assets),
        "yes" if isi_html else "no",
        coverage.coverage_ratio * 100,
    )
    if coverage.uncovered_tokens:
        logger.info("Uncovered signal tokens: %s", coverage.uncovered_tokens)

    return IngestionResult(
        claims=all_claims,
        assets=all_assets,
        isi_html=isi_html,
        embeddings=embeddings,
        coverage=coverage,
    )


def _deduplicate_claims(claims: list[ExtractedClaim]) -> list[ExtractedClaim]:
    seen: dict[str, ExtractedClaim] = {}
    for claim in claims:
        key = claim.text.strip().lower()
        if key not in seen:
            seen[key] = claim
    return list(seen.values())
