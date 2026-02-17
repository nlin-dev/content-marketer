from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from anthropic import AsyncAnthropic

from app.ingestion import strip_code_fences
from app.ingestion.pdf_parser import PageContent
from app.models.claim import ClaimCategory

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {c.value for c in ClaimCategory}

BATCH_SIZE = 3

SYSTEM_PROMPT = """\
You are extracting promotional medical claims from a pharmaceutical document.

Extract factual, data-backed claims suitable for use in regulated marketing materials.
Each claim must be a specific, standalone statement with concrete data points (percentages, \
hazard ratios, p-values, survival times, dosing regimens, etc.) or approved positioning language.

For each claim, provide:
- text: The exact claim text as it should appear in marketing content
- category: One of: {categories}
- source_ref: A reference in format "{{filename}}#{{descriptive-tag}}" (e.g., "visual-aid.pdf#FRESCO-2-OS")

Return a JSON array of objects. Only include claims with specific data or approved language.
Do not include general background text, instructions, or headers."""


@dataclass
class ExtractedClaim:
    text: str
    category: str
    source_ref: str


async def extract_claims(
    pages: list[PageContent],
    filename: str,
    *,
    api_key: str,
    model: str = "claude-sonnet-4-20250514",
) -> list[ExtractedClaim]:
    if not pages:
        return []

    client = AsyncAnthropic(api_key=api_key)
    system = SYSTEM_PROMPT.format(
        categories=", ".join(sorted(VALID_CATEGORIES)),
    )

    all_claims: list[ExtractedClaim] = []
    for i in range(0, len(pages), BATCH_SIZE):
        batch = pages[i : i + BATCH_SIZE]
        page_text = "\n\n".join(
            f"--- Page {p.page_number} ({p.filename}) ---\n{p.text}" for p in batch
        )

        msg = await client.messages.create(
            model=model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": page_text}],
        )

        response_text = msg.content[0].text
        claims = _parse_response(response_text, filename)
        all_claims.extend(claims)

    return all_claims


def _parse_response(text: str, filename: str) -> list[ExtractedClaim]:
    cleaned = strip_code_fences(text)
    try:
        items = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Failed to parse claim extraction response as JSON")
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

        claims.append(ExtractedClaim(text=text, category=category, source_ref=source_ref))

    return claims
