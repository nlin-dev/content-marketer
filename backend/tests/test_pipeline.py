import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.ingestion.pipeline import IngestionResult, classify_pdf, run_pipeline

DATA_DIR = Path(__file__).resolve().parent.parent / "fixtures"
VISUAL_AID = DATA_DIR / "visual-aid.pdf"
PRESCRIPTION = DATA_DIR / "medication-prescription.pdf"


MOCK_CLAIMS = json.dumps([
    {"text": "OS improved to 7.4 months", "category": "efficacy_os", "source_ref": "test.pdf#os"},
])
MOCK_ASSETS = json.dumps([
    {"slug": "km-curve", "name": "KM Curve", "asset_type": "image", "source_page": "p7"},
])
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
        assert result.claims_count > 0
        assert result.assets_count > 0
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

            mock_embed.return_value = [[0.0] * 1536]

            result = await run_pipeline(
                [VISUAL_AID, PRESCRIPTION],
                anthropic_api_key="fake",
                openai_api_key="fake",
            )

        # Same claim text from every batch -> dedup to 1
        assert result.claims_count == 1
