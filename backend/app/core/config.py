from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Knowledge Platform API"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg2://knowledge:knowledge@localhost:5432/knowledge"
    storage_dir: str = "./storage"
    cors_origins: list[str] = ["http://localhost:3000"]
    default_chunk_size: int = 1200
    default_chunk_overlap: int = 200

    qdrant_url: str = "http://qdrant:6333"
    qdrant_api_key: str | None = None
    qdrant_collection_name: str = "document_chunks"

    embedding_provider: str = "fastembed"
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    embedding_dimension: int = 384
    embedding_batch_size: int = 64

    reranking_enabled: bool = True
    rerank_top_n: int = 24
    rerank_provider: str = "local_embedding"
    rerank_model_name: str = "embedding-similarity-v1"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
