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


# Matches section headers like "5 WARNINGS AND PRECAUTIONS" or "5.1 Hypertension".
# First word after number must be >=2 uppercase-starting chars (avoids "4 mg", "3 times").
# Allows mixed case. Uses $ with trailing \s* to handle trailing whitespace in PDFs.
_SECTION_HEADER_RE = re.compile(
    r"^(\d+(?:\.\d+)?)\s{1,4}([A-Z][A-Za-z][A-Za-z &,./\-\(\)#'\d]*[A-Za-z)])\s*$",
    re.MULTILINE,
)

_SECTION_HEADER_FALLBACK_RE = _SECTION_HEADER_RE


def extract_sections_from_text(
    full_text: str,
    filename: str,
    page_offsets: list[tuple[int, int, int]] | None = None,
) -> list[SectionContent]:
    if not full_text.strip():
        return []

    if page_offsets is None:
        page_offsets = [(0, len(full_text), 1)]

    # Try primary regex first, fall back to lenient pattern
    matches = list(_SECTION_HEADER_RE.finditer(full_text))
    if not matches:
        matches = list(_SECTION_HEADER_FALLBACK_RE.finditer(full_text))
    if not matches:
        return []

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

    return [s for s in raw.values() if len(s.text.strip()) > 10]


def extract_sections(pdf_path: Path) -> list[SectionContent]:
    filename = pdf_path.name
    pages = extract_pages(pdf_path)
    if not pages:
        return []

    full_text = ""
    page_offsets: list[tuple[int, int, int]] = []
    for p in pages:
        start = len(full_text)
        full_text += p.text
        end = len(full_text)
        page_offsets.append((start, end, p.page_number))

    return extract_sections_from_text(full_text, filename, page_offsets)


def _offset_to_page(offset: int, page_offsets: list[tuple[int, int, int]]) -> int:
    for start, end, page_num in page_offsets:
        if start <= offset < end:
            return page_num
    # Default to last page
    return page_offsets[-1][2] if page_offsets else 1
