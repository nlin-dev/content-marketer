from pathlib import Path

import pytest

from app.ingestion.pdf_parser import PageContent, SectionContent, extract_pages, extract_sections, render_page_image, is_image_only

DATA_DIR = Path(__file__).resolve().parent.parent / "fixtures"
VISUAL_AID = DATA_DIR / "visual-aid.pdf"
PRESCRIPTION = DATA_DIR / "medication-prescription.pdf"


@pytest.fixture
def visual_aid_pages() -> list[PageContent]:
    return extract_pages(VISUAL_AID)


@pytest.fixture
def prescription_pages() -> list[PageContent]:
    return extract_pages(PRESCRIPTION)


class TestExtractPages:
    def test_returns_pages_from_visual_aid(self, visual_aid_pages: list[PageContent]):
        assert len(visual_aid_pages) > 0

    def test_page_content_has_text(self, visual_aid_pages: list[PageContent]):
        for page in visual_aid_pages:
            assert isinstance(page.text, str)
            assert isinstance(page.page_number, int)

    def test_page_numbers_are_sequential(self, visual_aid_pages: list[PageContent]):
        numbers = [p.page_number for p in visual_aid_pages]
        assert numbers == list(range(1, len(visual_aid_pages) + 1))

    def test_filename_is_set(self, visual_aid_pages: list[PageContent]):
        for page in visual_aid_pages:
            assert page.filename == "visual-aid.pdf"

    def test_prescription_pdf_has_pages(self, prescription_pages: list[PageContent]):
        assert len(prescription_pages) > 0

    def test_prescription_contains_fruzaqla(self, prescription_pages: list[PageContent]):
        all_text = " ".join(p.text for p in prescription_pages)
        assert "FRUZAQLA" in all_text or "fruquintinib" in all_text.lower()

    def test_visual_aid_pages_are_image_only(self, visual_aid_pages: list[PageContent]):
        image_only_pages = [p for p in visual_aid_pages if not p.has_text]
        assert len(image_only_pages) > 0


class TestRenderPageImage:
    def test_returns_png_bytes(self):
        result = render_page_image(VISUAL_AID, 1)
        assert isinstance(result, bytes)
        assert result[:8] == b"\x89PNG\r\n\x1a\n"

    def test_respects_dpi(self):
        low = render_page_image(VISUAL_AID, 1, dpi=72)
        high = render_page_image(VISUAL_AID, 1, dpi=150)
        assert len(high) > len(low)


class TestIsImageOnly:
    def test_visual_aid_is_image_only(self, visual_aid_pages: list[PageContent]):
        assert is_image_only(visual_aid_pages) is True

    def test_prescription_is_not_image_only(self, prescription_pages: list[PageContent]):
        assert is_image_only(prescription_pages) is False


class TestExtractSections:
    def test_extracts_numbered_sections_from_prescription(self):
        sections = extract_sections(PRESCRIPTION)
        assert len(sections) > 0

    def test_sections_have_titles(self):
        sections = extract_sections(PRESCRIPTION)
        for section in sections:
            assert section.title
            assert section.section_id

    def test_finds_warnings_section(self):
        sections = extract_sections(PRESCRIPTION)
        warning_sections = [s for s in sections if "warning" in s.title.lower()]
        assert len(warning_sections) > 0

    def test_finds_adverse_reactions_section(self):
        sections = extract_sections(PRESCRIPTION)
        ar_sections = [s for s in sections if "adverse" in s.title.lower()]
        assert len(ar_sections) > 0

    def test_section_text_is_nonempty(self):
        sections = extract_sections(PRESCRIPTION)
        for section in sections:
            assert len(section.text.strip()) > 0

    def test_section_has_page_range(self):
        sections = extract_sections(PRESCRIPTION)
        for section in sections:
            start, end = section.page_range
            assert start >= 1
            assert end >= start
