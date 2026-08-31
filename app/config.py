"""Application configuration loaded from environment variables.

Centralizing configuration here keeps secrets and environment-specific
settings out of application code, per the security requirements in the
project brief (all secrets must come from environment variables).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load a local .env file if present. In production, real environment
# variables set by the host/platform should take precedence and this is a
# no-op if no .env file exists.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    """Simple settings object populated from environment variables."""

    # Database: defaults to a local SQLite file for easy local development.
    # Set DATABASE_URL to a MySQL-compatible URL (e.g.
    # "******host/dbname") to use MySQL in production.
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'resumai.db'}"
    )

    # AI provider configuration. The AI service is built against an
    # OpenAI-compatible API so any compatible provider (OpenAI, Azure
    # OpenAI, local proxies, etc.) can be used by changing these values.
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_API_BASE_URL: str = os.getenv("AI_API_BASE_URL", "https://api.openai.com/v1")
    AI_MODEL: str = os.getenv("AI_MODEL", "gpt-4o-mini")

    # Basic admin credentials. Intentionally simple per requirements -
    # no full auth system for the first version.
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "changeme")

    # Used to sign session cookies.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-insecure-secret-key")

    # Directory containing the professional knowledge base source files.
    DATA_DIR: Path = BASE_DIR / "data"

    # The name this profile is about - used in prompts and templates.
    PROFILE_OWNER_NAME: str = os.getenv("PROFILE_OWNER_NAME", "Ryan")


settings = Settings()
