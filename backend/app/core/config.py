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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
