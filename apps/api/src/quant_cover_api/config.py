from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    postgres_db: str = "quant_cover"
    postgres_user: str = "quant_cover"
    postgres_password: str = "quant_cover"
    postgres_port: int = 5432
    database_url: str = "postgresql+psycopg://quant_cover:quant_cover@postgres:5432/quant_cover"

    model_config = SettingsConfigDict(case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
