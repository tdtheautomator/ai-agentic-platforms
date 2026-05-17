"""
Configuration management for IT Support Demo.

Centralized configuration loading from environment variables with sensible defaults.
All paths are auto-created if missing.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


class Config:
    """Centralized configuration for IT Support demo."""

    # Service Identity
    SERVICE_NAME: str = "IT Support Demo"
    SERVICE_PORT: int = 8007

    # LLM Backend
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "").strip()
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen3:0.6b")

    # Data Paths (auto-created in from_env)
    DATA_DIR: Path = None
    SQLITE_PATH: Path = None
    CHROMA_DIR: Path = None

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379")

    # Memory
    CTX_LIMIT: int = 10

    # Prometheus
    PROMETHEUS_ENABLED: bool = True

    @classmethod
    def from_env(cls) -> "Config":
        """Load and validate configuration from environment variables."""
        # Set paths
        cls.DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
        cls.SQLITE_PATH = cls.DATA_DIR / "sqlite" / "itsupport.db"
        cls.CHROMA_DIR = cls.DATA_DIR / "chroma"

        # Create directories if missing
        cls.SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.CHROMA_DIR.mkdir(parents=True, exist_ok=True)

        # Log configuration
        print(f"[{cls.SERVICE_NAME}] Configuration loaded:")
        print(f"  Service: {cls.SERVICE_NAME} (port {cls.SERVICE_PORT})")
        print(f"  LLM: {cls.OLLAMA_HOST}")
        print(f"  Data: {cls.DATA_DIR}")
        print(f"  Redis: {cls.REDIS_URL}")
        print(f"  Context limit: {cls.CTX_LIMIT}")

        return cls
