"""Application settings, loaded from environment variables.

Concept: the "12-factor" approach keeps configuration out of source code.
Secrets (API keys, DB passwords) live in the environment or a local .env file
that is never committed to git. See `.env.example` for every supported setting.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Reads a .env file if one exists; real environment variables take precedence.
load_dotenv()


def _get_int(name: str, default: int) -> int:
    """Read an integer environment variable, falling back to a default."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer, got {raw!r}") from exc


@dataclass(frozen=True)
class Settings:
    """Immutable settings object (frozen so it cannot be changed by accident)."""

    env: str
    log_level: str
    upload_dir: Path
    max_upload_bytes: int
    max_pdf_pages: int
    min_text_chars: int

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from the current environment."""
        return cls(
            env=os.getenv("TRUSTAI_ENV", "development"),
            log_level=os.getenv("TRUSTAI_LOG_LEVEL", "INFO").upper(),
            upload_dir=Path(os.getenv("TRUSTAI_UPLOAD_DIR", "data/uploads")),
            max_upload_bytes=_get_int("TRUSTAI_MAX_UPLOAD_MB", 20) * 1024 * 1024,
            max_pdf_pages=_get_int("TRUSTAI_MAX_PDF_PAGES", 500),
            min_text_chars=_get_int("TRUSTAI_MIN_TEXT_CHARS", 20),
        )


def get_settings() -> Settings:
    """Return settings read fresh from the environment.

    Not cached on purpose: tests can change env vars and get new values.
    The cost is negligible for Phase 1.
    """
    return Settings.from_env()
