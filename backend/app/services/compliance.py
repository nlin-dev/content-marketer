import re

from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approved_asset import ApprovedAsset
from app.models.claim import Claim, ClaimCategory
from app.models.compliance import ComplianceRecord, ComplianceStatus
from app.services.claim_validator import best_substring_match

EFFICACY_CATEGORIES = {
    ClaimCategory.EFFICACY_OS,
    ClaimCategory.EFFICACY_PFS,
    ClaimCategory.DCR,
    ClaimCategory.QOL,
    ClaimCategory.SUBGROUPS,
}


def _make_result(check_name: str, status: str, details: str) -> dict:
    return {"check_name": check_name, "status": status, "details": details}


def check_claims_present(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    elements = soup.find_all(attrs={"data-claim-id": True})
    if not elements:
        return _make_result("claims_present", "fail", "No data-claim-id elements found")
    return _make_result(
        "claims_present", "pass", f"Found {len(elements)} claim elements"
    )


def check_unapproved_content(
    html: str, claims: list[tuple[str, str]]
) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    # Remove claim-tagged elements
    for el in soup.find_all(attrs={"data-claim-id": True}):
        el.decompose()
    # Remove ISI section
    for el in soup.find_all(attrs={"data-isi": True}):
        el.decompose()

    remaining_text = soup.get_text(separator=" ", strip=True)
    if not claims or len(remaining_text) <= 50:
        return _make_result(
            "unapproved_content", "pass", "No significant unclaimed text"
        )

    # Check segments of remaining text
    segments = [s.strip() for s in remaining_text.split(".") if len(s.strip()) > 50]
    unapproved = []
    for segment in segments:
        best_score = max(
            (best_substring_match(segment, ct) for _, ct in claims), default=0.0
        )
        if best_score < 0.65:
            unapproved.append(segment[:80])

    if unapproved:
        return _make_result(
            "unapproved_content",
            "fail",
            f"{len(unapproved)} unapproved text segments: {unapproved[:3]}",
        )
    return _make_result("unapproved_content", "pass", "All text maps to claims")


def check_isi_present(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    isi = soup.find(attrs={"data-isi": "true"})
    if not isi:
        return _make_result("isi_present", "fail", "No data-isi element found")
    return _make_result("isi_present", "pass", "ISI section found")


def check_fair_balance(html: str, claims: list[dict]) -> dict:
    has_efficacy = any(c.get("category") in EFFICACY_CATEGORIES for c in claims)
    has_safety = any(c.get("category") == ClaimCategory.SAFETY for c in claims)
    if has_efficacy and not has_safety:
        return _make_result(
            "fair_balance",
            "fail",
            "Efficacy claims present without safety claims",
        )
    return _make_result("fair_balance", "pass", "Fair balance maintained")


def check_claim_statuses(claim_records: list[Claim]) -> dict:
    inactive = [c.id for c in claim_records if not c.is_active]
    if inactive:
        return _make_result(
            "claim_statuses", "fail", f"Inactive claims referenced: {inactive}"
        )
    return _make_result("claim_statuses", "pass", "All claims active")


def check_asset_compliance(html: str, approved_asset_ids: set[str]) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    elements = soup.find_all(attrs={"data-asset-id": True})
    unknown = [
        el["data-asset-id"]
        for el in elements
        if el["data-asset-id"] not in approved_asset_ids
    ]
    if unknown:
        return _make_result(
            "asset_compliance", "fail", f"Unapproved assets: {unknown}"
        )
    return _make_result("asset_compliance", "pass", "All assets approved")


def check_channel_spec(html: str) -> dict:
    issues = []
    soup = BeautifulSoup(html, "html.parser")

    if soup.find("script"):
        return _make_result(
            "channel_spec", "fail", "Script tags found in email content"
        )

    if soup.find("link", rel="stylesheet"):
        issues.append("External stylesheets found")

    if len(html.encode("utf-8")) > 100 * 1024:
        issues.append("Content exceeds 100KB")

    if issues:
        return _make_result("channel_spec", "warning", "; ".join(issues))
    return _make_result("channel_spec", "pass", "Email channel specs met")


def check_grammar_spelling(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    issues = []

    # Repeated consecutive words
    repeated = re.findall(r"\b(\w+)\s+\1\b", text, re.IGNORECASE)
    if repeated:
        issues.append(f"Repeated words: {repeated[:5]}")

    # Unclosed HTML-like patterns in text nodes
    for node in soup.find_all(string=True):
        node_text = str(node).strip()
        opens = node_text.count("<")
        closes = node_text.count(">")
        if opens != closes:
            issues.append("Unclosed HTML-like pattern in text")
            break

    # Missing capitalization after periods
    caps_issues = re.findall(r"\.\s+[a-z]", text)
    if caps_issues:
        issues.append(f"Missing capitalization after period ({len(caps_issues)} instances)")

    if issues:
        return _make_result("grammar_spelling", "warning", "; ".join(issues))
    return _make_result("grammar_spelling", "pass", "No grammar issues detected")


async def run_compliance_checks(
    html: str,
    db: AsyncSession,
    content_version_id: str,
    claim_ids: list[str],
    asset_ids: list[str],
) -> dict:
    claim_result = await db.execute(
        select(Claim).where(Claim.id.in_(claim_ids))
    )
    claim_records = list(claim_result.scalars().all())

    asset_result = await db.execute(
        select(ApprovedAsset).where(ApprovedAsset.id.in_(asset_ids))
    )
    asset_records = list(asset_result.scalars().all())
    approved_asset_id_set = {a.id for a in asset_records}

    claim_tuples = [(c.id, c.text) for c in claim_records]
    claim_dicts = [{"category": c.category, "id": c.id} for c in claim_records]

    checks = [
        check_claims_present(html),
        check_unapproved_content(html, claim_tuples),
        check_isi_present(html),
        check_fair_balance(html, claim_dicts),
        check_claim_statuses(claim_records),
        check_asset_compliance(html, approved_asset_id_set),
        check_channel_spec(html),
        check_grammar_spelling(html),
    ]

    for check in checks:
        record = ComplianceRecord(
            content_version_id=content_version_id,
            check_name=check["check_name"],
            status=ComplianceStatus(check["status"]),
            details={"message": check["details"]},
        )
        db.add(record)
    await db.flush()

    is_compliant = all(c["status"] in ("pass", "warning") for c in checks)
    can_export = all(c["status"] == "pass" for c in checks)

    return {
        "checks": checks,
        "is_compliant": is_compliant,
        "can_export": can_export,
    }
