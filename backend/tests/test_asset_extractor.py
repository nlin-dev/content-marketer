import json
from unittest.mock import AsyncMock, patch

import pytest

from app.ingestion.asset_extractor import ExtractedAsset, extract_assets
from app.ingestion.pdf_parser import PageContent


def _make_pages(n: int = 3, has_text: bool = True) -> list[PageContent]:
    return [
        PageContent(page_number=i + 1, text=f"Page {i+1} content" if has_text else "", filename="visual-aid.pdf", has_text=has_text)
        for i in range(n)
    ]


MOCK_ASSETS_JSON = json.dumps({"assets": [
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
]})


@pytest.mark.asyncio
async def test_extract_assets_validates_asset_type(mock_anthropic_response):
    bad_json = json.dumps({"assets": [
        {"slug": "good", "name": "Good Asset", "asset_type": "image", "source_page": "p1"},
        {"slug": "bad", "name": "Bad Asset", "asset_type": "invalid_type", "source_page": "p2"},
    ]})
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
async def test_extract_assets_uses_vision_for_image_only_pages(mock_anthropic_response, tmp_path):
    """When pages are image-only and pdf_path is provided, sends image content blocks."""
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), "hidden")
    pdf_path = tmp_path / "test.pdf"
    doc.save(str(pdf_path))
    doc.close()

    pages = _make_pages(n=1, has_text=False)

    with patch("app.ingestion.asset_extractor.AsyncAnthropic") as mock_cls:
        client = AsyncMock()
        mock_cls.return_value = client
        client.messages.create = AsyncMock(return_value=mock_anthropic_response('{"assets": []}'))

        await extract_assets(pages, "visual-aid.pdf", api_key="fake-key", pdf_path=pdf_path)

    assert client.messages.create.call_count == 1
    call_args = client.messages.create.call_args
    content = call_args.kwargs["messages"][0]["content"]
    assert isinstance(content, list)
    assert content[0]["type"] == "image"
