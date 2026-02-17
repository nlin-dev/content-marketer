from difflib import SequenceMatcher


def best_substring_match(text: str, claim_text: str) -> float:
    text_lower = text.lower()
    claim_lower = claim_text.lower()

    if len(claim_lower) >= len(text_lower):
        return SequenceMatcher(None, text_lower, claim_lower).ratio()

    best = 0.0
    window = len(claim_lower)
    for i in range(len(text_lower) - window + 1):
        substring = text_lower[i : i + window]
        ratio = SequenceMatcher(None, substring, claim_lower).ratio()
        if ratio > best:
            best = ratio
    return best


def validate_text_against_claims(
    text: str, claims: list[tuple[str, str]]
) -> list[dict]:
    results = []
    for claim_id, claim_text in claims:
        ratio = best_substring_match(text, claim_text)
        results.append(
            {
                "claim_id": claim_id,
                "claim_text": claim_text,
                "match_ratio": ratio,
                "is_verbatim": ratio >= 0.85,
            }
        )
    return results
