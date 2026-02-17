from __future__ import annotations

import logging

from anthropic import AsyncAnthropic

from app.ingestion import strip_code_fences
from app.ingestion.pdf_parser import SectionContent

logger = logging.getLogger(__name__)

# Sections that contain ISI-relevant content in a prescribing information PDF
ISI_SECTION_PREFIXES = ("section-5", "section-6", "section-7", "section-8")

FALLBACK_ISI = '<div data-isi="true" data-editable="false"><p>Important Safety Information not available.</p></div>'

SYSTEM_PROMPT = """\
You are formatting Important Safety Information (ISI) from a pharmaceutical prescribing \
information document into clean HTML.

Output requirements:
- Wrap everything in a single <div data-isi="true" data-editable="false">
- Use <h2> for major section headings (WARNINGS AND PRECAUTIONS, ADVERSE REACTIONS, etc.)
- Use <h3> for subsection headings (Hypertension, Hemorrhagic Events, etc.)
- Use <p> for body text
- Preserve all specific data: percentages, incidence rates, grade information
- Include the INDICATION section at the top if present
- Do NOT add any content not present in the source text
- Output raw HTML only, no markdown fences"""


async def extract_isi_html(
    sections: list[SectionContent],
    *,
    api_key: str,
    model: str = "claude-sonnet-4-20250514",
) -> str:
    relevant = [s for s in sections if any(s.section_id.startswith(p) for p in ISI_SECTION_PREFIXES)]

    if not relevant:
        logger.warning("No ISI-relevant sections found, returning fallback")
        return FALLBACK_ISI

    client = AsyncAnthropic(api_key=api_key)
    section_text = "\n\n".join(
        f"=== {s.title} (Section {s.section_id}) ===\n{s.text}" for s in relevant
    )

    msg = await client.messages.create(
        model=model,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": section_text}],
    )

    html = strip_code_fences(msg.content[0].text)

    # Ensure wrapper div exists
    if 'data-isi="true"' not in html:
        html = f'<div data-isi="true" data-editable="false">\n{html}\n</div>'

    return html
