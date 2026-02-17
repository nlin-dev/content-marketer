from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from anthropic import AsyncAnthropic

from app.ingestion import strip_code_fences
from app.ingestion.pdf_parser import PageContent
from app.models.approved_asset import AssetType

logger = logging.getLogger(__name__)

VALID_ASSET_TYPES = {t.value for t in AssetType}

SYSTEM_PROMPT = """\
You are identifying visual assets from a pharmaceutical marketing visual aid PDF.

For each distinct figure, chart, graph, diagram, table, or image referenced in the pages, extract:
- slug: A URL-safe identifier (lowercase, hyphens, e.g., "km-curve-os-fresco2")
- name: A descriptive name (e.g., "KM Curve OS FRESCO-2")
- asset_type: One of: {asset_types}
- source_page: The page reference (e.g., "p7")

Return a JSON array of objects. Only include distinct visual elements, not decorative imagery or \
background graphics. Focus on clinical figures, data charts, study designs, and branded diagrams."""


@dataclass
class ExtractedAsset:
    slug: str
    name: str
    asset_type: str
    source_page: str
    filename: str


async def extract_assets(
    pages: list[PageContent],
    filename: str,
    *,
    api_key: str,
    model: str = "claude-sonnet-4-20250514",
) -> list[ExtractedAsset]:
    if not pages:
        return []

    client = AsyncAnthropic(api_key=api_key)
    system = SYSTEM_PROMPT.format(asset_types=", ".join(sorted(VALID_ASSET_TYPES)))

    page_text = "\n\n".join(
        f"--- Page {p.page_number} ({p.filename}) ---\n{p.text}" for p in pages
    )

    msg = await client.messages.create(
        model=model,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": page_text}],
    )

    response_text = msg.content[0].text.strip()
    return _parse_response(response_text, filename)


def _parse_response(text: str, filename: str) -> list[ExtractedAsset]:
    cleaned = strip_code_fences(text)
    try:
        items = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Failed to parse asset extraction response as JSON")
        return []

    assets: list[ExtractedAsset] = []
    for item in items:
        asset_type = item.get("asset_type", "")
        if asset_type not in VALID_ASSET_TYPES:
            logger.warning("Skipping asset with invalid type: %s", asset_type)
            continue

        slug = item.get("slug", "").strip()
        name = item.get("name", "").strip()
        if not slug or not name:
            continue

        assets.append(
            ExtractedAsset(
                slug=slug,
                name=name,
                asset_type=asset_type,
                source_page=item.get("source_page", ""),
                filename=filename,
            )
        )

    return assets
