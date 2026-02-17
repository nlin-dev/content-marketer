import openai

from app.config import settings


async def generate_embedding(text: str) -> list[float]:
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.embeddings.create(
        model=settings.openai_embedding_model, input=text
    )
    return response.data[0].embedding


async def batch_generate_embeddings(texts: list[str]) -> list[list[float]]:
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.embeddings.create(
        model=settings.openai_embedding_model, input=texts
    )
    return [item.embedding for item in response.data]
