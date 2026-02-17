from __future__ import annotations


def strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:])
        if "```" in cleaned:
            cleaned = cleaned[: cleaned.rindex("```")]
    return cleaned.strip()
