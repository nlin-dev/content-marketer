import json
from unittest.mock import AsyncMock, patch

import pytest

from app.ingestion.claim_extractor import ExtractedClaim, extract_claims
from app.ingestion.pdf_parser import PageContent


def _make_pages(texts: list[str], filename: str = "test.pdf", has_text: bool = True) -> list[PageContent]:
    return [PageContent(page_number=i + 1, text=t, filename=filename, has_text=has_text) for i, t in enumerate(texts)]


MOCK_RESPONSE_JSON = json.dumps({"claims": [
    {
        "text": "FRUZAQLA improved overall survival to 7.4 months vs 4.8 months (HR=0.66)",
        "category": "efficacy_os",
        "source_ref": "test.pdf#efficacy-os-data",
    },
    {
        "text": "Hypertension occurred in 49% of patients",
        "category": "safety",
        "source_ref": "test.pdf#safety-hypertension",
    },
]})


@pytest.mark.asyncio
async def test_extract_claims_validates_categories(mock_anthropic_response):
    bad_json = json.dumps({"claims": [
        {"text": "Valid claim", "category": "efficacy_os", "source_ref": "test.pdf#a"},
        {"text": "Bad category", "category": "not_a_category", "source_ref": "test.pdf#b"},
    ]})
    pages = _make_pages(["Some text"])
    with patch("app.ingestion.claim_extractor.AsyncAnthropic") as mock_cls:
        client = AsyncMock()
        mock_cls.return_value = client
        client.messages.create = AsyncMock(return_value=mock_anthropic_response(bad_json))

        result = await extract_claims(pages, "test.pdf", api_key="fake-key")

    assert len(result) == 1
    assert result[0].category == "efficacy_os"


@pytest.mark.asyncio
async def test_extract_claims_sets_source_ref(mock_anthropic_response):
    pages = _make_pages(["Data page"])
    with patch("app.ingestion.claim_extractor.AsyncAnthropic") as mock_cls:
        client = AsyncMock()
        mock_cls.return_value = client
        client.messages.create = AsyncMock(return_value=mock_anthropic_response(MOCK_RESPONSE_JSON))

        result = await extract_claims(pages, "test.pdf", api_key="fake-key")

    assert all(c.source_ref.startswith("test.pdf#") for c in result)


@pytest.mark.asyncio
async def test_extract_claims_batches_pages(mock_anthropic_response):
    pages = _make_pages(["p1", "p2", "p3", "p4", "p5"], filename="doc.pdf")
    with patch("app.ingestion.claim_extractor.AsyncAnthropic") as mock_cls:
        client = AsyncMock()
        mock_cls.return_value = client
        client.messages.create = AsyncMock(return_value=mock_anthropic_response('{"claims": []}'))

        await extract_claims(pages, "doc.pdf", api_key="fake-key")

    # 5 pages batched by 3 = 2 API calls
    assert client.messages.create.call_count == 2


@pytest.mark.asyncio
async def test_extract_claims_handles_empty_pages():
    result = await extract_claims([], "empty.pdf", api_key="fake-key")
    assert result == []


@pytest.mark.asyncio
async def test_extract_claims_uses_vision_for_image_only_pages(mock_anthropic_response, tmp_path):
    """When pages are image-only and pdf_path is provided, sends image content blocks."""
    # Create a minimal valid PDF for rendering
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), "hidden")  # need something to render
    pdf_path = tmp_path / "test.pdf"
    doc.save(str(pdf_path))
    doc.close()

    pages = _make_pages([""], filename="test.pdf", has_text=False)

    with patch("app.ingestion.claim_extractor.AsyncAnthropic") as mock_cls:
        client = AsyncMock()
        mock_cls.return_value = client
        client.messages.create = AsyncMock(return_value=mock_anthropic_response('{"claims": []}'))

        await extract_claims(pages, "test.pdf", api_key="fake-key", pdf_path=pdf_path)

    # Vision batch size is 2, so 2 pages = 1 call
    assert client.messages.create.call_count == 1
    call_args = client.messages.create.call_args
    content = call_args.kwargs["messages"][0]["content"]
    # Should be a list of content blocks (image + text pairs)
    assert isinstance(content, list)
    assert content[0]["type"] == "image"
    assert content[1]["type"] == "text"
