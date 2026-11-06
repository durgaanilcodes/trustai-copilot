"""FastAPI application: Phase 1 exposes document upload and inspection.

Run:  uvicorn trustai.api.main:app --reload
Docs: http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from trustai import __version__
from trustai.config import get_settings
from trustai.exceptions import (
    DocumentNotFoundError,
    EmptyFileError,
    ExtractionError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from trustai.ingestion import ingest_bytes
from trustai.logging_config import configure_logging
from trustai.storage import LocalDocumentStore

configure_logging(get_settings().log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title="TrustAI", version=__version__, description="Enterprise Knowledge Copilot")


def _store() -> LocalDocumentStore:
    """Create the store from current settings (cheap; just a folder handle)."""
    return LocalDocumentStore(get_settings().upload_dir)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "ok", "version": __version__}


@app.post("/documents", status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)) -> dict[str, Any]:
    """Upload a PDF or TXT, extract its text, and store it."""
    settings = get_settings()
    # Read at most limit+1 bytes so an oversized upload cannot exhaust memory.
    data = await file.read(settings.max_upload_bytes + 1)
    try:
        document = ingest_bytes(file.filename or "unnamed", data, settings)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(exc)) from exc
    except FileTooLargeError as exc:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, str(exc)) from exc
    except (EmptyFileError, ExtractionError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    document_id = _store().save(document, data)
    return {"document_id": document_id, "metadata": document.to_dict()["metadata"]}


@app.get("/documents")
def list_documents() -> list[dict[str, Any]]:
    """List stored documents with their metadata."""
    store = _store()
    return [
        {"document_id": doc_id, "metadata": store.get(doc_id).to_dict()["metadata"]}
        for doc_id in store.list_ids()
    ]


@app.get("/documents/{document_id}")
def get_document(document_id: str) -> dict[str, Any]:
    """Return one document's metadata and per-page extracted text."""
    try:
        document = _store().get(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return {"document_id": document_id, **document.to_dict()}


@app.delete("/documents/{document_id}")
def delete_document(document_id: str) -> JSONResponse:
    """Delete a stored document."""
    try:
        _store().delete(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return JSONResponse({"deleted": document_id})
