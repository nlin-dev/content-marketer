import json
from unittest.mock import AsyncMock, patch

import pytest

from app.ingestion.asset_extractor import ExtractedAsset, extract_assets
from app.ingestion.pdf_parser import PageContent


def _make_pages(n: int = 3) -> list[PageContent]:
    return [
        PageContent(page_number=i + 1, text=f"Page {i+1} content", filename="visual-aid.pdf")
        for i in range(n)
    ]


MOCK_ASSETS_JSON = json.dumps([
    {
        "slug": "km-curve-os-fresco2",
        "name": "KM Curve OS FRESCO-2",
        "asset_type": "image",
        "source_page": "p7",
    },
    {
        "slug": "moa-kinome-selectivity",
        "name": "MOA Kinome Selectivity",
        "asset_type": "infographic",
        "source_page": "p3",
    },
])


@pytest.mark.asyncio
async def test_extract_assets_returns_list(mock_anthropic_response):
    pages = _make_pages()
    with patch("app.ingestion.asset_extractor.AsyncAnthropic") as mock_cls:
        client = AsyncMock()
        mock_cls.return_value = client
        client.messages.create = AsyncMock(return_value=mock_anthropic_response(MOCK_ASSETS_JSON))

        result = await extract_assets(pages, "visual-aid.pdf", api_key="fake-key")

    assert len(result) == 2
    assert all(isinstance(a, ExtractedAsset) for a in result)


@pytest.mark.asyncio
async def test_extract_assets_validates_asset_type(mock_anthropic_response):
    bad_json = json.dumps([
        {"slug": "good", "name": "Good Asset", "asset_type": "image", "source_page": "p1"},
        {"slug": "bad", "name": "Bad Asset", "asset_type": "invalid_type", "source_page": "p2"},
    ])
    pages = _make_pages()
    with patch("app.ingestion.asset_extractor.AsyncAnthropic") as mock_cls:
        client = AsyncMock()
        mock_cls.return_value = client
        client.messages.create = AsyncMock(return_value=mock_anthropic_response(bad_json))

        result = await extract_assets(pages, "visual-aid.pdf", api_key="fake-key")

    assert len(result) == 1
    assert result[0].asset_type == "image"


@pytest.mark.asyncio
async def test_extract_assets_empty_pages():
    result = await extract_assets([], "empty.pdf", api_key="fake-key")
    assert result == []


@pytest.mark.asyncio
async def test_extract_assets_sets_filename(mock_anthropic_response):
    pages = _make_pages()
    with patch("app.ingestion.asset_extractor.AsyncAnthropic") as mock_cls:
        client = AsyncMock()
        mock_cls.return_value = client
        client.messages.create = AsyncMock(return_value=mock_anthropic_response(MOCK_ASSETS_JSON))

        result = await extract_assets(pages, "visual-aid.pdf", api_key="fake-key")

    assert all(a.filename == "visual-aid.pdf" for a in result)
