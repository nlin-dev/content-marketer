from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = (
        "postgresql+asyncpg://contentmarketer:contentmarketer_dev@localhost:5432/contentmarketer"
    )
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    anthropic_model: str = "claude-sonnet-4-20250514"


settings = Settings()
