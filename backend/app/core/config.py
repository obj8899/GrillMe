"""Application configuration settings using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for GrillMe backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Project metadata
    project_name: str = "GrillMe Backend API"
    version: str = "0.1.0"
    description: str = (
        "AI-powered mock technical interviewer for a developer's own GitHub projects"
    )

    # Runtime environment
    environment: str = "development"
    debug: bool = True

    # Server binding
    host: str = "127.0.0.1"
    port: int = 8000

    # Cross-Origin Resource Sharing
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


settings = Settings()
