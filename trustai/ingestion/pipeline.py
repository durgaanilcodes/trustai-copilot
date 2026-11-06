"""Ingestion pipeline: bytes in, ExtractedDocument out.

validate -> extract -> clean -> measure metadata -> reject if there is no text.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Optional

from trustai.config import Settings, get_settings
from trustai.exceptions import ExtractionError
from trustai.ingestion.cleaning import clean_text
from trustai.ingestion.extractors import RawExtraction, extract_pdf, extract_txt
from trustai.ingestion.models import DocumentMetadata, ExtractedDocument, PageText
from trustai.ingestion.validation import sanitize_filename, validate_upload

logger = logging.getLogger(__name__)


def ingest_bytes(
    filename: str, data: bytes, settings: Optional[Settings] = None
) -> ExtractedDocument:
    """Validate and extract a document from raw bytes.

    Raises:
        UnsupportedFileTypeError, EmptyFileError, FileTooLargeError: bad upload.
        ExtractionError: unreadable file, or no extractable text (e.g. scanned PDF).
    """
    settings = settings or get_settings()
    safe_name = sanitize_filename(filename)
    file_type = validate_upload(safe_name, data, settings.max_upload_bytes)

    raw: RawExtraction
    if file_type == "pdf":
        raw = extract_pdf(data, max_pages=settings.max_pdf_pages)
    else:
        raw = extract_txt(data)

    pages = tuple(
        PageText(page_number=i, text=clean_text(text)) for i, text in enumerate(raw.pages, start=1)
    )
    total_chars = sum(len(p.text) for p in pages)
    if total_chars < settings.min_text_chars:
        raise ExtractionError(
            "No extractable text found. If this is a scanned PDF, it needs OCR, "
            "which is not supported yet."
        )

    metadata = DocumentMetadata(
        filename=safe_name,
        file_type=file_type,
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        page_count=len(pages),
        char_count=total_chars,
        word_count=sum(len(p.text.split()) for p in pages),
        title=raw.title,
        author=raw.author,
        created=raw.created,
        encoding=raw.encoding,
        empty_pages=tuple(p.page_number for p in pages if not p.text),
    )
    logger.info(
        "Ingested %s (%s, %d pages, %d chars)", safe_name, file_type, len(pages), total_chars
    )
    return ExtractedDocument(metadata=metadata, pages=pages)
