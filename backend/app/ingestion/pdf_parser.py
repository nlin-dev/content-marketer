from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass
class PageContent:
    page_number: int
    text: str
    filename: str


@dataclass
class SectionContent:
    section_id: str
    title: str
    text: str
    page_range: tuple[int, int]
    filename: str


def extract_pages(pdf_path: Path) -> list[PageContent]:
    filename = pdf_path.name
    pages: list[PageContent] = []
    with fitz.open(pdf_path) as doc:
        for i, page in enumerate(doc):
            text = page.get_text()
            pages.append(PageContent(page_number=i + 1, text=text, filename=filename))
    return pages


# Matches top-level prescribing info section headers like "5 WARNINGS AND PRECAUTIONS"
# and subsections like "5.1 Hypertension"
_SECTION_HEADER_RE = re.compile(
    r"^(\d+(?:\.\d+)?)\s+([A-Z][A-Z &,/\-\(\)]+(?:\n[A-Z][A-Z &,/\-\(\)]+)*)",
    re.MULTILINE,
)


def extract_sections(pdf_path: Path) -> list[SectionContent]:
    filename = pdf_path.name
    pages = extract_pages(pdf_path)
    if not pages:
        return []

    # Build a single text with page markers so we can map back to page numbers
    page_marker = "\n<<PAGE:{}>>\n"
    full_text = ""
    page_offsets: list[tuple[int, int, int]] = []  # (start_offset, end_offset, page_num)
    for p in pages:
        start = len(full_text)
        full_text += p.text
        end = len(full_text)
        page_offsets.append((start, end, p.page_number))
        full_text += page_marker.format(p.page_number)

    # Find all section headers
    matches = list(_SECTION_HEADER_RE.finditer(full_text))
    if not matches:
        return []

    # Collect raw sections, then merge duplicates (highlights TOC vs full content)
    raw: dict[str, SectionContent] = {}
    for i, match in enumerate(matches):
        section_num = match.group(1)
        title = match.group(2).strip()
        title = re.sub(r"\s+", " ", title)

        body_start = match.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        text = full_text[body_start:body_end].strip()

        start_page = _offset_to_page(match.start(), page_offsets)
        end_page = _offset_to_page(body_end - 1, page_offsets)

        key = f"section-{section_num}"
        if key in raw:
            # Merge: keep the longer text (full content over highlights stub)
            existing = raw[key]
            if len(text) > len(existing.text):
                raw[key] = SectionContent(
                    section_id=key,
                    title=title,
                    text=text,
                    page_range=(min(existing.page_range[0], start_page), max(existing.page_range[1], end_page)),
                    filename=filename,
                )
        else:
            raw[key] = SectionContent(
                section_id=key,
                title=title,
                text=text,
                page_range=(start_page, end_page),
                filename=filename,
            )

    # Filter out sections with no meaningful content
    return [s for s in raw.values() if len(s.text.strip()) > 10]


def _offset_to_page(offset: int, page_offsets: list[tuple[int, int, int]]) -> int:
    for start, end, page_num in page_offsets:
        if start <= offset < end:
            return page_num
    # Default to last page
    return page_offsets[-1][2] if page_offsets else 1
