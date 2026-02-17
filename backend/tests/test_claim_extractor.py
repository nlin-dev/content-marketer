import json
from unittest.mock import AsyncMock, patch

import pytest

from app.ingestion.claim_extractor import (
    ExtractedClaim,
    create_sliding_window_batches,
    extract_claims,
    _parse_response,
)
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


# --- Sliding Window Batches ---


class TestSlidingWindowBatches:
    def test_no_overlap(self):
        items = list(range(6))
        batches = create_sliding_window_batches(items, window=3, overlap=0)
        assert batches == [[0, 1, 2], [3, 4, 5]]

    def test_overlap_one(self):
        items = list(range(6))
        batches = create_sliding_window_batches(items, window=3, overlap=1)
        assert batches == [[0, 1, 2], [2, 3, 4], [4, 5]]

    def test_fewer_than_window(self):
        items = [1, 2]
        batches = create_sliding_window_batches(items, window=5, overlap=1)
        assert batches == [[1, 2]]

    def test_empty_input(self):
        assert create_sliding_window_batches([], window=3, overlap=1) == []

    def test_exact_window_size(self):
        items = [1, 2, 3]
        batches = create_sliding_window_batches(items, window=3, overlap=1)
        assert batches == [[1, 2, 3]]

    def test_overlap_zero_with_remainder(self):
        items = list(range(5))
        batches = create_sliding_window_batches(items, window=3, overlap=0)
        assert batches == [[0, 1, 2], [3, 4]]


@pytest.mark.asyncio
async def test_extract_claims_uses_sliding_window(mock_anthropic_response):
    """Text mode uses overlap=1, producing more API calls than non-overlapping."""
    pages = _make_pages(["p1", "p2", "p3", "p4", "p5", "p6"], filename="doc.pdf")
    with patch("app.ingestion.claim_extractor.AsyncAnthropic") as mock_cls:
        client = AsyncMock()
        mock_cls.return_value = client
        client.messages.create = AsyncMock(return_value=mock_anthropic_response('{"claims": []}'))

        await extract_claims(pages, "doc.pdf", api_key="fake-key")

    # 6 pages, window=3, overlap=1 -> batches at [0:3], [2:5], [4:6] = 3 calls
    assert client.messages.create.call_count == 3


# --- Confidence Scoring ---


class TestConfidenceScoring:
    def test_parse_response_extracts_confidence(self):
        data = json.dumps({"claims": [
            {"text": "Claim A", "category": "efficacy_os", "source_ref": "f#a", "confidence": 0.92},
        ]})
        claims = _parse_response(data, "f")
        assert claims[0].confidence == 0.92

    def test_parse_response_defaults_confidence(self):
        data = json.dumps({"claims": [
            {"text": "Claim A", "category": "efficacy_os", "source_ref": "f#a"},
        ]})
        claims = _parse_response(data, "f")
        assert claims[0].confidence == 0.5

    def test_parse_response_clamps_confidence_high(self):
        data = json.dumps({"claims": [
            {"text": "Claim A", "category": "efficacy_os", "source_ref": "f#a", "confidence": 1.5},
        ]})
        claims = _parse_response(data, "f")
        assert claims[0].confidence == 1.0

    def test_parse_response_clamps_confidence_low(self):
        data = json.dumps({"claims": [
            {"text": "Claim A", "category": "efficacy_os", "source_ref": "f#a", "confidence": -0.3},
        ]})
        claims = _parse_response(data, "f")
        assert claims[0].confidence == 0.0


# --- Two-Pass Extraction ---


@pytest.mark.asyncio
async def test_two_pass_filters_rejected_claims(mock_anthropic_response):
    """Second pass should remove claims rejected by validation."""
    pages = _make_pages(["Some clinical data"], filename="doc.pdf")

    first_pass = json.dumps({"claims": [
        {"text": "Claim A valid", "category": "efficacy_os", "source_ref": "doc.pdf#a", "confidence": 0.9},
        {"text": "Claim B dubious", "category": "safety", "source_ref": "doc.pdf#b", "confidence": 0.4},
    ]})
    second_pass = json.dumps({"validated": [
        {"text": "Claim A valid", "category": "efficacy_os", "source_ref": "doc.pdf#a", "confidence": 0.95, "status": "confirmed"},
        {"text": "Claim B dubious", "category": "safety", "source_ref": "doc.pdf#b", "confidence": 0.2, "status": "rejected"},
    ]})

    call_count = 0

    async def mock_create(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_anthropic_response(first_pass)
        return mock_anthropic_response(second_pass)

    with patch("app.ingestion.claim_extractor.AsyncAnthropic") as mock_cls:
        client = AsyncMock()
        mock_cls.return_value = client
        client.messages.create = AsyncMock(side_effect=mock_create)

        result = await extract_claims(pages, "doc.pdf", api_key="fake-key", two_pass=True)

    assert len(result) == 1
    assert result[0].text == "Claim A valid"
    assert result[0].confidence == 0.95


@pytest.mark.asyncio
async def test_two_pass_off_by_default(mock_anthropic_response):
    pages = _make_pages(["Some data"], filename="doc.pdf")
    with patch("app.ingestion.claim_extractor.AsyncAnthropic") as mock_cls:
        client = AsyncMock()
        mock_cls.return_value = client
        client.messages.create = AsyncMock(return_value=mock_anthropic_response(MOCK_RESPONSE_JSON))

        result = await extract_claims(pages, "doc.pdf", api_key="fake-key")

    # Only 1 API call (no second pass)
    assert client.messages.create.call_count == 1
    assert len(result) == 2
