"""Local-disk document store (Phase 1 only).

Layout:  <upload_dir>/<document_id>/original.<ext>   (the uploaded bytes)
                                   /extracted.json    (metadata + per-page text)

Phase 2 replaces this with PostgreSQL + pgvector. The interface (save / get /
list / delete) is kept small so that swap is easy.
"""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from trustai.exceptions import DocumentNotFoundError
from trustai.ingestion.models import ExtractedDocument


class LocalDocumentStore:
    """Stores uploaded documents and their extracted text on local disk."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, document: ExtractedDocument, original_bytes: bytes) -> str:
        """Persist a document and return its new id (a random UUID)."""
        document_id = str(uuid.uuid4())
        folder = self.root / document_id
        folder.mkdir(parents=True)
        ext = "pdf" if document.metadata.file_type == "pdf" else "txt"
        (folder / f"original.{ext}").write_bytes(original_bytes)
        (folder / "extracted.json").write_text(
            json.dumps(document.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return document_id

    def get(self, document_id: str) -> ExtractedDocument:
        """Load a stored document, or raise DocumentNotFoundError."""
        path = self._folder(document_id) / "extracted.json"
        if not path.is_file():
            raise DocumentNotFoundError(f"Document {document_id} not found.")
        return ExtractedDocument.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list_ids(self) -> list[str]:
        """Return ids of all stored documents (oldest first by folder mtime)."""
        folders = [p for p in self.root.iterdir() if (p / "extracted.json").is_file()]
        return [p.name for p in sorted(folders, key=lambda p: p.stat().st_mtime)]

    def delete(self, document_id: str) -> None:
        """Delete a stored document, or raise DocumentNotFoundError."""
        folder = self._folder(document_id)
        if not (folder / "extracted.json").is_file():
            raise DocumentNotFoundError(f"Document {document_id} not found.")
        shutil.rmtree(folder)

    def _folder(self, document_id: str) -> Path:
        """Resolve an id to its folder.

        Security: ids must be valid UUIDs. This blocks path traversal such as
        '../../etc' because such strings cannot parse as a UUID.
        """
        try:
            normalized = str(uuid.UUID(document_id))
        except (ValueError, AttributeError, TypeError) as exc:
            raise DocumentNotFoundError(f"Document {document_id!r} not found.") from exc
        return self.root / normalized
