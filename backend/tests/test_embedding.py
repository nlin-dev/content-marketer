from unittest.mock import AsyncMock, patch

import pytest

from app.services.embedding import EMBEDDING_DIM, batch_generate_embeddings, generate_embedding


@pytest.mark.asyncio
async def test_generate_embedding_returns_zero_vector_on_exception():
    with patch("app.services.embedding.settings") as mock_settings:
        mock_settings.openai_api_key = "fake-key"
        mock_settings.openai_embedding_model = "text-embedding-3-small"
        with patch("app.services.embedding.openai.AsyncOpenAI") as mock_cls:
            client = AsyncMock()
            mock_cls.return_value = client
            client.embeddings.create.side_effect = Exception("API error")

            result = await generate_embedding("test")

    assert len(result) == EMBEDDING_DIM
    assert all(v == 0.0 for v in result)


@pytest.mark.asyncio
async def test_batch_generate_embeddings_returns_zero_vectors_on_exception():
    with patch("app.services.embedding.settings") as mock_settings:
        mock_settings.openai_api_key = "fake-key"
        mock_settings.openai_embedding_model = "text-embedding-3-small"
        with patch("app.services.embedding.openai.AsyncOpenAI") as mock_cls:
            client = AsyncMock()
            mock_cls.return_value = client
            client.embeddings.create.side_effect = Exception("API error")

            result = await batch_generate_embeddings(["a", "b"])

    assert len(result) == 2
    assert all(len(v) == EMBEDDING_DIM for v in result)
    assert all(all(x == 0.0 for x in v) for v in result)


@pytest.mark.asyncio
async def test_generate_embedding_returns_zero_vector_when_no_api_key():
    with patch("app.services.embedding.settings") as mock_settings:
        mock_settings.openai_api_key = ""

        result = await generate_embedding("test")

    assert len(result) == EMBEDDING_DIM
    assert all(v == 0.0 for v in result)


@pytest.mark.asyncio
async def test_batch_generate_embeddings_returns_zero_vectors_when_no_api_key():
    with patch("app.services.embedding.settings") as mock_settings:
        mock_settings.openai_api_key = ""

        result = await batch_generate_embeddings(["a", "b"])

    assert len(result) == 2
    assert all(len(v) == EMBEDDING_DIM for v in result)
