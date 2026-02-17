from pathlib import Path

import pytest

from app.ingestion.pdf_parser import (
    PageContent,
    SectionContent,
    extract_pages,
    extract_sections,
    extract_sections_from_text,
    render_page_image,
    is_image_only,
)

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

    def test_finds_warnings_subsections(self):
        sections = extract_sections(PRESCRIPTION)
        # Section 5 "WARNINGS AND PRECAUTIONS" has subsections like 5.1 Hypertension
        warning_subsections = [s for s in sections if s.section_id.startswith("section-5.")]
        assert len(warning_subsections) > 0

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


# --- Improved Section Extraction ---


class TestExtractSectionsFromText:
    def test_mixed_case_titles(self):
        text = "5.1 Hypertension\nBody text about hypertension.\n6 DOSING\nDosing info."
        sections = extract_sections_from_text(text, "test.pdf")
        titles = [s.title for s in sections]
        assert any("Hypertension" in t for t in titles)

    def test_title_case_with_conjunctions(self):
        text = "5.2 Diarrhea and Colitis\nSome body text here.\n6 NEXT SECTION\nMore text."
        sections = extract_sections_from_text(text, "test.pdf")
        titles = [s.title for s in sections]
        assert any("Diarrhea" in t for t in titles)

    def test_all_caps_still_works(self):
        text = "5 WARNINGS AND PRECAUTIONS\nWarning body.\n6 ADVERSE REACTIONS\nReaction body."
        sections = extract_sections_from_text(text, "test.pdf")
        assert len(sections) == 2

    def test_no_false_matches_on_body_text(self):
        text = "5 WARNINGS\nThe patient had 3 episodes of diarrhea.\nAnother line of body text."
        sections = extract_sections_from_text(text, "test.pdf")
        # "3 episodes" should NOT be parsed as a section header
        assert len(sections) == 1
        assert sections[0].title == "WARNINGS"

    def test_fallback_pattern_used(self):
        """When primary regex finds nothing, fallback catches mixed-case headers."""
        text = "Section 1: Introduction\nBody text.\nSection 2: Methods\nMore text."
        # This won't match either primary or fallback numbered patterns,
        # so should return empty (no false positives)
        sections = extract_sections_from_text(text, "test.pdf")
        # We only match numbered sections like "5.1 Title", not "Section 1:"
        assert len(sections) == 0
