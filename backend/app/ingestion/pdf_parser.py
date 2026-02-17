from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass
class PageContent:
    page_number: int
    text: str
    filename: str
    has_text: bool = True


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
            has_text = bool(text.strip())
            pages.append(PageContent(page_number=i + 1, text=text, filename=filename, has_text=has_text))
    return pages


def render_page_image(pdf_path: Path, page_number: int, dpi: int = 150) -> bytes:
    with fitz.open(pdf_path) as doc:
        page = doc[page_number - 1]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        return pix.tobytes("png")


def is_image_only(pages: list[PageContent]) -> bool:
    return len(pages) > 0 and all(not p.has_text for p in pages)


def build_image_content_blocks(
    pages: list[PageContent], pdf_path: Path, filename: str
) -> list[dict]:
    content_blocks: list[dict] = []
    for p in pages:
        png_bytes = render_page_image(pdf_path, p.page_number)
        b64 = base64.b64encode(png_bytes).decode()
        content_blocks.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": b64},
        })
        content_blocks.append({
            "type": "text",
            "text": f"(Page {p.page_number} of {filename})",
        })
    return content_blocks


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

    full_text = ""
    page_offsets: list[tuple[int, int, int]] = []  # (start_offset, end_offset, page_num)
    for p in pages:
        start = len(full_text)
        full_text += p.text
        end = len(full_text)
        page_offsets.append((start, end, p.page_number))

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
