from unittest.mock import AsyncMock, patch

import pytest

from app.ingestion.isi_extractor import extract_isi_html
from app.ingestion.pdf_parser import SectionContent

MOCK_ISI_HTML = """\
<div data-isi="true" data-editable="false">
<h2>WARNINGS AND PRECAUTIONS</h2>
<h3>Hypertension</h3>
<p>Hypertension occurred in 49% of patients. hemorrhagic events reported.</p>
<h2>ADVERSE REACTIONS</h2>
<p>Most common adverse reactions included thromboembolic events and embryo-fetal toxicity concerns.</p>
</div>"""


def _make_sections() -> list[SectionContent]:
    return [
        SectionContent(
            section_id="section-5",
            title="WARNINGS AND PRECAUTIONS",
            text="Hypertension occurred in 49% of 911 patients. Hemorrhagic events...",
            page_range=(5, 8),
            filename="medication-prescription.pdf",
        ),
        SectionContent(
            section_id="section-6",
            title="ADVERSE REACTIONS",
            text="Most common adverse reactions (>=20%) were hypertension...",
            page_range=(8, 12),
            filename="medication-prescription.pdf",
        ),
        SectionContent(
            section_id="section-7",
            title="DRUG INTERACTIONS",
            text="Avoid concomitant use with strong CYP3A inducers...",
            page_range=(12, 13),
            filename="medication-prescription.pdf",
        ),
    ]


@pytest.mark.asyncio
async def test_extract_isi_returns_html(mock_anthropic_response):
    sections = _make_sections()
    with patch("app.ingestion.isi_extractor.AsyncAnthropic") as mock_cls:
        client = AsyncMock()
        mock_cls.return_value = client
        client.messages.create = AsyncMock(return_value=mock_anthropic_response(MOCK_ISI_HTML))

        result = await extract_isi_html(sections, api_key="fake-key")

    assert "data-isi" in result
    assert "data-editable" in result


@pytest.mark.asyncio
async def test_extract_isi_contains_required_keywords(mock_anthropic_response):
    sections = _make_sections()
    with patch("app.ingestion.isi_extractor.AsyncAnthropic") as mock_cls:
        client = AsyncMock()
        mock_cls.return_value = client
        client.messages.create = AsyncMock(return_value=mock_anthropic_response(MOCK_ISI_HTML))

        result = await extract_isi_html(sections, api_key="fake-key")

    lower = result.lower()
    assert "hypertension" in lower
    assert "adverse reactions" in lower


@pytest.mark.asyncio
async def test_extract_isi_filters_relevant_sections(mock_anthropic_response):
    all_sections = _make_sections() + [
        SectionContent(
            section_id="section-14",
            title="CLINICAL STUDIES",
            text="FRESCO-2 was a randomized trial...",
            page_range=(15, 18),
            filename="medication-prescription.pdf",
        ),
    ]
    with patch("app.ingestion.isi_extractor.AsyncAnthropic") as mock_cls:
        client = AsyncMock()
        mock_cls.return_value = client
        client.messages.create = AsyncMock(return_value=mock_anthropic_response(MOCK_ISI_HTML))

        await extract_isi_html(all_sections, api_key="fake-key")

    # Verify only ISI-relevant sections were sent to Claude
    call_args = client.messages.create.call_args
    user_content = call_args.kwargs["messages"][0]["content"]
    assert "CLINICAL STUDIES" not in user_content


@pytest.mark.asyncio
async def test_extract_isi_empty_sections_returns_fallback():
    result = await extract_isi_html([], api_key="fake-key")
    assert "data-isi" in result
