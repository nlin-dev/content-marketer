import json
import math
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ingestion.claim_extractor import ExtractedClaim
from app.ingestion.pipeline import (
    CoverageReport,
    IngestionResult,
    classify_pdf,
    deduplicate_claims_with_embeddings,
    extract_signal_tokens,
    run_pipeline,
)
from app.ingestion.pdf_parser import is_image_only, extract_pages
from app.services.embedding import batch_generate_embeddings

DATA_DIR = Path(__file__).resolve().parent.parent / "fixtures"
VISUAL_AID = DATA_DIR / "visual-aid.pdf"
PRESCRIPTION = DATA_DIR / "medication-prescription.pdf"


MOCK_CLAIMS = json.dumps({"claims": [
    {"text": "OS improved to 7.4 months", "category": "efficacy_os", "source_ref": "test.pdf#os"},
]})
MOCK_ASSETS = json.dumps({"assets": [
    {"slug": "km-curve", "name": "KM Curve", "asset_type": "image", "source_page": "p7"},
]})
MOCK_ISI = '<div data-isi="true" data-editable="false"><h2>WARNINGS</h2><p>Hypertension 49%</p></div>'


def _patch_all_anthropic():
    return (
        patch("app.ingestion.claim_extractor.AsyncAnthropic"),
        patch("app.ingestion.isi_extractor.AsyncAnthropic"),
        patch("app.ingestion.asset_extractor.AsyncAnthropic"),
    )


class TestClassifyPdf:
    def test_classifies_prescription(self):
        assert classify_pdf(PRESCRIPTION) == "prescribing_info"

    def test_classifies_visual_aid(self):
        assert classify_pdf(VISUAL_AID) == "visual_aid"


class TestVisionDetection:
    def test_visual_aid_is_image_only(self):
        pages = extract_pages(VISUAL_AID)
        assert is_image_only(pages) is True

    def test_prescription_is_not_image_only(self):
        pages = extract_pages(PRESCRIPTION)
        assert is_image_only(pages) is False


class TestRunPipeline:
    @pytest.mark.asyncio
    async def test_returns_ingestion_result(self, mock_anthropic_response):
        p1, p2, p3 = _patch_all_anthropic()
        with p1 as m1, p2 as m2, p3 as m3, patch(
            "app.ingestion.pipeline.batch_generate_embeddings"
        ) as mock_embed:
            for m in (m1, m2, m3):
                client = AsyncMock()
                m.return_value = client
                client.messages.create = AsyncMock(return_value=mock_anthropic_response(MOCK_CLAIMS))

            # Override asset extractor to return assets
            asset_client = AsyncMock()
            m3.return_value = asset_client
            asset_client.messages.create = AsyncMock(return_value=mock_anthropic_response(MOCK_ASSETS))

            # Override ISI extractor to return ISI
            isi_client = AsyncMock()
            m2.return_value = isi_client
            isi_client.messages.create = AsyncMock(return_value=mock_anthropic_response(MOCK_ISI))

            mock_embed.return_value = [[0.0] * 1536]

            result = await run_pipeline(
                [VISUAL_AID, PRESCRIPTION],
                anthropic_api_key="fake",
                openai_api_key="fake",
            )

        assert isinstance(result, IngestionResult)
        assert len(result.claims) > 0
        assert len(result.assets) > 0
        assert result.isi_html is not None

    @pytest.mark.asyncio
    async def test_deduplicates_claims(self, mock_anthropic_response):
        p1, p2, p3 = _patch_all_anthropic()
        with p1 as m1, p2 as m2, p3 as m3, patch(
            "app.ingestion.pipeline.batch_generate_embeddings"
        ) as mock_embed:
            for m in (m1, m2, m3):
                client = AsyncMock()
                m.return_value = client
                client.messages.create = AsyncMock(return_value=mock_anthropic_response(MOCK_CLAIMS))

            # Override asset extractor to return assets
            asset_client = AsyncMock()
            m3.return_value = asset_client
            asset_client.messages.create = AsyncMock(return_value=mock_anthropic_response(MOCK_ASSETS))

            # Override ISI extractor to return ISI
            isi_client = AsyncMock()
            m2.return_value = isi_client
            isi_client.messages.create = AsyncMock(return_value=mock_anthropic_response(MOCK_ISI))

            mock_embed.return_value = [[0.0] * 1536]

            result = await run_pipeline(
                [VISUAL_AID, PRESCRIPTION],
                anthropic_api_key="fake",
                openai_api_key="fake",
            )

        # Same claim text from every batch -> dedup to 1
        assert len(result.claims) == 1


class TestBatchEmbeddingOrder:
    @pytest.mark.asyncio
    async def test_embeddings_sorted_by_index(self):
        """Verify batch_generate_embeddings returns embeddings sorted by index,
        even when the OpenAI API returns items in shuffled order."""
        emb_a = [0.1] * 4
        emb_b = [0.2] * 4
        emb_c = [0.3] * 4

        # Simulate OpenAI returning items out of order (indices 2, 0, 1)
        item_0 = MagicMock(index=2, embedding=emb_c)
        item_1 = MagicMock(index=0, embedding=emb_a)
        item_2 = MagicMock(index=1, embedding=emb_b)

        mock_response = MagicMock()
        mock_response.data = [item_0, item_1, item_2]

        with patch("app.services.embedding.settings") as mock_settings, \
             patch("app.services.embedding.openai.AsyncOpenAI") as mock_cls, \
             patch("app.services.embedding._client", None):
            mock_settings.openai_api_key = "fake-key"
            mock_settings.openai_embedding_model = "text-embedding-3-small"
            client = AsyncMock()
            mock_cls.return_value = client
            client.embeddings.create = AsyncMock(return_value=mock_response)

            result = await batch_generate_embeddings(["a", "b", "c"])

        assert result == [emb_a, emb_b, emb_c]


# --- Fuzzy Deduplication ---


def _make_claim(text: str, confidence: float = 0.5, category: str = "efficacy_os") -> ExtractedClaim:
    return ExtractedClaim(text=text, category=category, source_ref="f#a", confidence=confidence)


def _unit_vec(components: list[float]) -> list[float]:
    """Normalize a vector to unit length."""
    mag = math.sqrt(sum(c * c for c in components))
    return [c / mag for c in components]


class TestFuzzyDeduplication:
    def test_exact_duplicates_removed(self):
        c1 = _make_claim("Same claim", confidence=0.9)
        c2 = _make_claim("Same claim", confidence=0.8)
        # Identical embeddings
        emb = [1.0, 0.0, 0.0]
        result = deduplicate_claims_with_embeddings([c1, c2], [emb, emb], threshold=0.95)
        assert len(result) == 1
        assert result[0].confidence == 0.9  # higher confidence kept

    def test_near_duplicates_removed(self):
        c1 = _make_claim("OS improved to 7.4 months", confidence=0.9)
        c2 = _make_claim("Overall survival improved to 7.4 mo", confidence=0.7)
        # Very similar embeddings (cosine > 0.95)
        e1 = _unit_vec([1.0, 0.0, 0.0])
        e2 = _unit_vec([0.99, 0.1, 0.0])
        result = deduplicate_claims_with_embeddings([c1, c2], [e1, e2], threshold=0.95)
        assert len(result) == 1

    def test_dissimilar_claims_kept(self):
        c1 = _make_claim("OS improved to 7.4 months", confidence=0.9)
        c2 = _make_claim("Hypertension occurred in 49%", confidence=0.8)
        e1 = _unit_vec([1.0, 0.0, 0.0])
        e2 = _unit_vec([0.0, 1.0, 0.0])
        result = deduplicate_claims_with_embeddings([c1, c2], [e1, e2], threshold=0.95)
        assert len(result) == 2

    def test_empty_input(self):
        assert deduplicate_claims_with_embeddings([], [], threshold=0.95) == []

    def test_single_claim(self):
        c = _make_claim("Only claim")
        result = deduplicate_claims_with_embeddings([c], [[1.0, 0.0]], threshold=0.95)
        assert len(result) == 1


# --- Coverage Verification ---


class TestSignalTokenExtraction:
    def test_extracts_percentages(self):
        tokens = extract_signal_tokens("Hypertension occurred in 49% of patients")
        assert "49%" in tokens

    def test_extracts_hazard_ratios(self):
        tokens = extract_signal_tokens("HR=0.66, 95% CI")
        assert "HR=0.66" in tokens

    def test_extracts_p_values(self):
        tokens = extract_signal_tokens("p<0.001 was significant, also p=0.03")
        assert "p<0.001" in tokens
        assert "p=0.03" in tokens

    def test_extracts_time_measurements(self):
        tokens = extract_signal_tokens("OS was 7.4 months and PFS 3.7 months")
        assert "7.4 months" in tokens
        assert "3.7 months" in tokens

    def test_extracts_dosing(self):
        tokens = extract_signal_tokens("5 mg once daily for 21 days")
        assert "5 mg" in tokens

    def test_empty_text(self):
        assert extract_signal_tokens("") == set()


class TestCoverageReport:
    def test_uncovered_tokens_detected(self):
        source = "OS was 7.4 months (HR=0.66, p<0.001). Safety: hypertension 49%."
        claims_text = "OS improved to 7.4 months with HR=0.66"
        tokens = extract_signal_tokens(source)
        covered = {t for t in tokens if t in claims_text}
        uncovered = tokens - covered
        assert "49%" in uncovered
        assert "p<0.001" in uncovered

    def test_full_coverage(self):
        source = "HR=0.66"
        claims_text = "The hazard ratio was HR=0.66"
        tokens = extract_signal_tokens(source)
        covered = {t for t in tokens if t in claims_text}
        assert covered == tokens
