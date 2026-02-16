from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Tell Pydantic to read from .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "sqlite:///./abtest.db"

    # Application
    app_name: str = "AB Testing Framework"
    debug: bool = False

    # Statistics
    default_confidence_level: float = 0.95
    minimum_sample_size: int = 2

    # Storage
    storage_backend: str = "database"  # "memory" or "database"

    """
    class Config:  # this tells pydantic "Where should I load environment variables from?"
        env_file = ".env"
        env_file_encoding = "utf-8"

    # So instead of only reading system-level environment variables, it will also read from .env
    """


def get_settings() -> Settings:
    return Settings()
