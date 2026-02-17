from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from anthropic import AsyncAnthropic

from app.ingestion.pdf_parser import PageContent, build_image_content_blocks, is_image_only
from app.models.claim import ClaimCategory

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {c.value for c in ClaimCategory}

BATCH_SIZE = 3
BATCH_OVERLAP = 1
VISION_BATCH_SIZE = 2

SYSTEM_PROMPT = """\
You are extracting promotional medical claims from a pharmaceutical document.

Extract factual, data-backed claims suitable for use in regulated marketing materials.
Each claim must be a specific, standalone statement with concrete data points (percentages, \
hazard ratios, p-values, survival times, dosing regimens, etc.) or approved positioning language.

For each claim, provide:
- text: The exact claim text as it should appear in marketing content
- category: One of: {categories}
- source_ref: A reference in format "{{filename}}#{{descriptive-tag}}" (e.g., "visual-aid.pdf#FRESCO-2-OS")
- confidence: A float from 0.0 to 1.0 indicating how confident you are in the claim's accuracy

Return a JSON array of objects. Only include claims with specific data or approved language.
Do not include general background text, instructions, or headers."""

VALIDATION_PROMPT = """\
You are validating extracted medical claims against the source text.

For each claim, verify it is accurately supported by the source text below.
Return a JSON object with a "validated" array. For each claim, include:
- text: The claim text (may be refined for accuracy)
- category: The claim category
- source_ref: The source reference
- confidence: Updated confidence score (0.0-1.0)
- status: "confirmed" if the claim is accurate, "rejected" if not supported

Source text:
{source_text}

Claims to validate:
{claims_json}"""


T = TypeVar("T")


def create_sliding_window_batches(items: list[T], window: int, overlap: int) -> list[list[T]]:
    if not items:
        return []
    step = max(1, window - overlap)
    batches: list[list[T]] = []
    for i in range(0, len(items), step):
        batch = items[i : i + window]
        batches.append(batch)
        if i + window >= len(items):
            break
    return batches


@dataclass
class ExtractedClaim:
    text: str
    category: str
    source_ref: str
    confidence: float = 0.5


async def extract_claims(
    pages: list[PageContent],
    filename: str,
    *,
    api_key: str,
    model: str = "claude-sonnet-4-20250514",
    pdf_path: Path | None = None,
    two_pass: bool = False,
) -> list[ExtractedClaim]:
    if not pages:
        return []

    client = AsyncAnthropic(api_key=api_key)
    system = SYSTEM_PROMPT.format(
        categories=", ".join(sorted(VALID_CATEGORIES)),
    )

    use_vision = is_image_only(pages) and pdf_path is not None
    batch_size = VISION_BATCH_SIZE if use_vision else BATCH_SIZE
    overlap = 0 if use_vision else BATCH_OVERLAP

    batches = create_sliding_window_batches(pages, window=batch_size, overlap=overlap)

    all_claims: list[ExtractedClaim] = []
    for batch in batches:
        if use_vision:
            content = build_image_content_blocks(batch, pdf_path, filename)
        else:
            content = "\n\n".join(
                f"--- Page {p.page_number} ({p.filename}) ---\n{p.text}" for p in batch
            )

        msg = await client.messages.create(
            model=model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": content}],
        )

        response_text = msg.content[0].text
        claims = _parse_response(response_text, filename)
        all_claims.extend(claims)

    if two_pass and all_claims:
        all_claims = await _validate_claims(all_claims, pages, client=client, model=model)

    return all_claims


async def _validate_claims(
    claims: list[ExtractedClaim],
    pages: list[PageContent],
    *,
    client: AsyncAnthropic,
    model: str,
) -> list[ExtractedClaim]:
    source_text = "\n".join(p.text for p in pages)
    claims_data = [
        {"text": c.text, "category": c.category, "source_ref": c.source_ref, "confidence": c.confidence}
        for c in claims
    ]

    prompt = VALIDATION_PROMPT.format(
        source_text=source_text[:8000],
        claims_json=json.dumps(claims_data),
    )

    msg = await client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = msg.content[0].text
    try:
        data = json.loads(response_text)
        validated = data.get("validated", data) if isinstance(data, dict) else data
    except json.JSONDecodeError:
        logger.warning("Failed to parse validation response, returning original claims")
        return claims

    result: list[ExtractedClaim] = []
    for item in validated:
        if item.get("status") == "rejected":
            continue
        category = item.get("category", "")
        if category not in VALID_CATEGORIES:
            continue
        text = item.get("text", "").strip()
        if not text:
            continue
        confidence = item.get("confidence", 0.5)
        confidence = max(0.0, min(1.0, float(confidence)))
        result.append(ExtractedClaim(
            text=text,
            category=category,
            source_ref=item.get("source_ref", ""),
            confidence=confidence,
        ))

    return result


def _parse_response(text: str, filename: str) -> list[ExtractedClaim]:
    try:
        data = json.loads(text)
        items = data.get("claims", data) if isinstance(data, dict) else data
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse claim extraction response as JSON: %s — response: %.200s", e, text)
        return []

    claims: list[ExtractedClaim] = []
    for item in items:
        category = item.get("category", "")
        if category not in VALID_CATEGORIES:
            logger.warning("Skipping claim with invalid category: %s", category)
            continue

        text = item.get("text", "").strip()
        source_ref = item.get("source_ref", f"{filename}#unknown")
        if not text:
            continue

        confidence = item.get("confidence", 0.5)
        confidence = max(0.0, min(1.0, float(confidence)))

        claims.append(ExtractedClaim(text=text, category=category, source_ref=source_ref, confidence=confidence))

    return claims
