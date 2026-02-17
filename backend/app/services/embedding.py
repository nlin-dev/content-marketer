import logging

import openai

from app.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 1536

_client: openai.AsyncOpenAI | None = None


def _get_client() -> openai.AsyncOpenAI:
    global _client
    if _client is None:
        _client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def generate_embedding(text: str) -> list[float]:
    if not settings.openai_api_key:
        logger.warning("OpenAI API unavailable, returning zero vectors. Semantic search will not work.")
        return [0.0] * EMBEDDING_DIM
    try:
        client = _get_client()
        response = await client.embeddings.create(
            model=settings.openai_embedding_model, input=text
        )
        return response.data[0].embedding
    except Exception:
        logger.warning("OpenAI API unavailable, returning zero vectors. Semantic search will not work.")
        return [0.0] * EMBEDDING_DIM


async def batch_generate_embeddings(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if not settings.openai_api_key:
        logger.warning("OpenAI API unavailable, returning zero vectors. Semantic search will not work.")
        return [[0.0] * EMBEDDING_DIM for _ in texts]
    try:
        client = _get_client()
        response = await client.embeddings.create(
            model=settings.openai_embedding_model, input=texts
        )
        return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
    except Exception:
        logger.warning("OpenAI API unavailable, returning zero vectors. Semantic search will not work.")
        return [[0.0] * EMBEDDING_DIM for _ in texts]
