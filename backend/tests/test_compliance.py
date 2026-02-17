"""Tests for all 8 compliance check functions."""

from unittest.mock import MagicMock

from app.models.claim import ClaimCategory
from app.services.compliance import (
    check_asset_compliance,
    check_channel_spec,
    check_claim_statuses,
    check_claims_present,
    check_fair_balance,
    check_grammar_spelling,
    check_isi_present,
    check_unapproved_content,
)


# ---------------------------------------------------------------------------
# 1. check_claims_present
# ---------------------------------------------------------------------------

class TestCheckClaimsPresent:
    def test_pass_with_claim_elements(self):
        html = '<div><span data-claim-id="c1">Claim text</span></div>'
        result = check_claims_present(html)
        assert result["status"] == "pass"
        assert result["check_name"] == "claims_present"

    def test_fail_without_claim_elements(self):
        html = "<div><p>No claims here</p></div>"
        result = check_claims_present(html)
        assert result["status"] == "fail"

    def test_pass_with_multiple_claims(self):
        html = '<span data-claim-id="c1">A</span><span data-claim-id="c2">B</span>'
        result = check_claims_present(html)
        assert result["status"] == "pass"
        assert "2" in result["details"]


# ---------------------------------------------------------------------------
# 2. check_isi_present
# ---------------------------------------------------------------------------

class TestCheckIsiPresent:
    def test_pass_with_isi_element(self):
        html = '<div><section data-isi="true">ISI content</section></div>'
        result = check_isi_present(html)
        assert result["status"] == "pass"
        assert result["check_name"] == "isi_present"

    def test_fail_without_isi_element(self):
        html = "<div><p>No ISI here</p></div>"
        result = check_isi_present(html)
        assert result["status"] == "fail"


# ---------------------------------------------------------------------------
# 3. check_asset_compliance
# ---------------------------------------------------------------------------

class TestCheckAssetCompliance:
    def test_pass_all_assets_approved(self):
        html = '<img data-asset-id="a1"/><img data-asset-id="a2"/>'
        result = check_asset_compliance(html, {"a1", "a2"})
        assert result["status"] == "pass"
        assert result["check_name"] == "asset_compliance"

    def test_fail_unapproved_asset(self):
        html = '<img data-asset-id="a1"/><img data-asset-id="a999"/>'
        result = check_asset_compliance(html, {"a1"})
        assert result["status"] == "fail"
        assert "a999" in result["details"]

    def test_pass_no_assets(self):
        html = "<div>No assets</div>"
        result = check_asset_compliance(html, set())
        assert result["status"] == "pass"


# ---------------------------------------------------------------------------
# 4. check_channel_spec
# ---------------------------------------------------------------------------

class TestCheckChannelSpec:
    def test_pass_clean_email(self):
        html = "<div><p>Clean email content</p></div>"
        result = check_channel_spec(html)
        assert result["status"] == "pass"
        assert result["check_name"] == "channel_spec"

    def test_fail_script_tags(self):
        html = "<div><script>alert('xss')</script></div>"
        result = check_channel_spec(html)
        assert result["status"] == "fail"

    def test_warning_external_stylesheet(self):
        html = '<link rel="stylesheet" href="https://example.com/style.css"/><p>Content</p>'
        result = check_channel_spec(html)
        assert result["status"] == "warning"
        assert "stylesheet" in result["details"].lower()

    def test_warning_large_content(self):
        html = "<div>" + "x" * (101 * 1024) + "</div>"
        result = check_channel_spec(html)
        assert result["status"] == "warning"
        assert "100KB" in result["details"]


# ---------------------------------------------------------------------------
# 5. check_grammar_spelling
# ---------------------------------------------------------------------------

class TestCheckGrammarSpelling:
    def test_pass_clean_text(self):
        html = "<p>This is clean text. Nothing wrong here.</p>"
        result = check_grammar_spelling(html)
        assert result["status"] == "pass"
        assert result["check_name"] == "grammar_spelling"

    def test_warning_repeated_words(self):
        html = "<p>The the quick brown fox.</p>"
        result = check_grammar_spelling(html)
        assert result["status"] == "warning"
        assert "Repeated" in result["details"]

    def test_warning_missing_capitalization(self):
        html = "<p>First sentence. second sentence.</p>"
        result = check_grammar_spelling(html)
        assert result["status"] == "warning"
        assert "capitalization" in result["details"].lower()


# ---------------------------------------------------------------------------
# 6. check_unapproved_content
# ---------------------------------------------------------------------------

class TestCheckUnapprovedContent:
    def test_pass_all_text_maps_to_claims(self):
        html = '<div><span data-claim-id="c1">This drug improves outcomes significantly in patients.</span></div>'
        claims = [("c1", "This drug improves outcomes significantly in patients.")]
        result = check_unapproved_content(html, claims)
        assert result["status"] == "pass"
        assert result["check_name"] == "unapproved_content"

    def test_fail_unapproved_long_segment(self):
        # Text outside claim elements that doesn't match any claim
        long_text = "This is a completely unapproved statement that has no matching claim text whatsoever and is quite long indeed."
        html = f'<div><p>{long_text}</p></div>'
        claims = [("c1", "Something totally different from the paragraph above")]
        result = check_unapproved_content(html, claims)
        assert result["status"] == "fail"
        assert "unapproved" in result["details"].lower()

    def test_pass_no_claims_short_text(self):
        html = "<div>Short</div>"
        result = check_unapproved_content(html, [])
        assert result["status"] == "pass"


# ---------------------------------------------------------------------------
# 7. check_fair_balance
# ---------------------------------------------------------------------------

class TestCheckFairBalance:
    def test_pass_efficacy_and_safety(self):
        claims = [
            {"category": ClaimCategory.EFFICACY_OS, "id": "c1"},
            {"category": ClaimCategory.SAFETY, "id": "c2"},
        ]
        result = check_fair_balance("<div></div>", claims)
        assert result["status"] == "pass"
        assert result["check_name"] == "fair_balance"

    def test_fail_efficacy_without_safety(self):
        claims = [
            {"category": ClaimCategory.EFFICACY_PFS, "id": "c1"},
        ]
        result = check_fair_balance("<div></div>", claims)
        assert result["status"] == "fail"
        assert "safety" in result["details"].lower()

    def test_pass_safety_only(self):
        claims = [{"category": ClaimCategory.SAFETY, "id": "c1"}]
        result = check_fair_balance("<div></div>", claims)
        assert result["status"] == "pass"

    def test_pass_no_claims(self):
        result = check_fair_balance("<div></div>", [])
        assert result["status"] == "pass"

    def test_fail_qol_without_safety(self):
        claims = [{"category": ClaimCategory.QOL, "id": "c1"}]
        result = check_fair_balance("<div></div>", claims)
        assert result["status"] == "fail"


# ---------------------------------------------------------------------------
# 8. check_claim_statuses
# ---------------------------------------------------------------------------

class TestCheckClaimStatuses:
    def _mock_claim(self, claim_id: str, is_active: bool) -> MagicMock:
        claim = MagicMock()
        claim.id = claim_id
        claim.is_active = is_active
        return claim

    def test_pass_all_active(self):
        claims = [self._mock_claim("c1", True), self._mock_claim("c2", True)]
        result = check_claim_statuses(claims)
        assert result["status"] == "pass"
        assert result["check_name"] == "claim_statuses"

    def test_fail_inactive_claim(self):
        claims = [self._mock_claim("c1", True), self._mock_claim("c2", False)]
        result = check_claim_statuses(claims)
        assert result["status"] == "fail"
        assert "c2" in result["details"]

    def test_pass_empty_list(self):
        result = check_claim_statuses([])
        assert result["status"] == "pass"

    def test_fail_multiple_inactive(self):
        claims = [
            self._mock_claim("c1", False),
            self._mock_claim("c2", False),
            self._mock_claim("c3", True),
        ]
        result = check_claim_statuses(claims)
        assert result["status"] == "fail"
        assert "c1" in result["details"]
        assert "c2" in result["details"]
