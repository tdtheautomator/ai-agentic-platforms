"""
Configuration management for banking-demo.

Centralized configuration using Pydantic Settings.
Loads from environment variables and .env file.
"""

from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings from environment variables.
    
    All configuration values are loaded from environment variables
    or .env file. Provides type-safe access to configuration.
    
    Attributes:
        openai_api_key: OpenAI API key (optional).
        anthropic_api_key: Anthropic API key (optional).
        ollama_host: Ollama server URL.
        ollama_model: Ollama model name.
        data_dir: Directory for persistent data (SQLite, ChromaDB).
        redis_url: Redis connection URL.
        context_limit: Maximum in-context memory turns.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """

    # LLM Configuration
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ollama_host: str = "http://host.docker.internal:11434"
    ollama_model: str = "qwen3:0.6b"

    # Data Paths
    data_dir: Path = Path("/data")

    # Redis Configuration
    redis_url: str = "redis://redis:6379"

    # Context Configuration
    context_limit: int = 10

    # Logging Configuration
    log_level: str = "INFO"

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
