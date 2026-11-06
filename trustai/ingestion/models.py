"""Data structures passed between ingestion steps.

Concept: we keep text *per page* (not one giant string) because Phase 3 needs
page numbers to produce accurate source citations like "policy.pdf, page 4".
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class PageText:
    """Cleaned text of one page. Page numbers start at 1."""

    page_number: int
    text: str


@dataclass(frozen=True)
class DocumentMetadata:
    """Facts about a document that are measured, not guessed."""

    filename: str
    file_type: str  # "pdf" or "txt"
    size_bytes: int
    sha256: str  # fingerprint of the original bytes; same file -> same hash
    page_count: int
    char_count: int
    word_count: int
    title: Optional[str] = None  # from PDF info dictionary, if present
    author: Optional[str] = None
    created: Optional[str] = None  # raw PDF creation date string, if present
    encoding: Optional[str] = None  # detected text encoding (TXT only)
    empty_pages: tuple[int, ...] = field(default_factory=tuple)  # pages with no text


@dataclass(frozen=True)
class ExtractedDocument:
    """Result of ingestion: metadata plus cleaned per-page text."""

    metadata: DocumentMetadata
    pages: tuple[PageText, ...]

    @property
    def full_text(self) -> str:
        """All pages joined, separated by blank lines."""
        return "\n\n".join(p.text for p in self.pages if p.text)

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable representation (used for storage)."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExtractedDocument":
        """Rebuild from `to_dict()` output."""
        meta = dict(data["metadata"])
        meta["empty_pages"] = tuple(meta.get("empty_pages", ()))
        pages = tuple(PageText(**p) for p in data["pages"])
        return cls(metadata=DocumentMetadata(**meta), pages=pages)
