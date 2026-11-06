"""Text extraction from PDF and TXT bytes.

Known limits (documented on purpose, not hidden):
  * No OCR: scanned/image-only PDFs yield no text and are rejected upstream.
  * Tables and multi-column layouts are flattened into plain text by pypdf.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Optional

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from trustai.exceptions import ExtractionError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RawExtraction:
    """Un-cleaned extraction output: per-page text plus format-specific facts."""

    pages: list[str]
    title: Optional[str] = None
    author: Optional[str] = None
    created: Optional[str] = None
    encoding: Optional[str] = None


def extract_pdf(data: bytes, max_pages: int) -> RawExtraction:
    """Extract text page by page from PDF bytes.

    Raises:
        ExtractionError: corrupt file, password-protected file, or too many pages.
    """
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            # Many PDFs are "encrypted" with an empty user password; try that first.
            if not reader.decrypt(""):
                raise ExtractionError("PDF is password-protected and cannot be read.")
        page_total = len(reader.pages)
        if page_total > max_pages:
            raise ExtractionError(f"PDF has {page_total} pages; the limit is {max_pages}.")

        pages: list[str] = []
        for index, page in enumerate(reader.pages, start=1):
            try:
                pages.append(page.extract_text() or "")
            except Exception as exc:  # one bad page should not kill the whole document
                logger.warning("Could not extract page %d: %s", index, exc)
                pages.append("")

        info = reader.metadata
        return RawExtraction(
            pages=pages,
            title=_clean_meta(getattr(info, "title", None)),
            author=_clean_meta(getattr(info, "author", None)),
            created=_clean_meta(info.get("/CreationDate") if info else None),
        )
    except ExtractionError:
        raise
    except (PdfReadError, ValueError, KeyError, OSError) as exc:
        raise ExtractionError(f"Could not read PDF: {exc}") from exc
    except Exception as exc:  # pypdf can raise assorted errors on malformed files
        raise ExtractionError(f"Could not read PDF: {type(exc).__name__}: {exc}") from exc


def extract_txt(data: bytes) -> RawExtraction:
    """Decode TXT bytes to text, detecting the encoding.

    Order tried: UTF-8 with BOM, UTF-8, UTF-16 (only if a BOM is present), then
    Windows-1252 as a last resort (it decodes almost any byte sequence, so the
    reported encoding is a best guess for legacy files).
    A file containing NUL bytes is treated as binary and rejected.
    """
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            return RawExtraction(pages=[data.decode("utf-16")], encoding="utf-16")
        except UnicodeDecodeError as exc:
            raise ExtractionError("File looks like UTF-16 but could not be decoded.") from exc

    if b"\x00" in data:
        raise ExtractionError("File contains binary data and is not a plain text file.")

    for encoding in ("utf-8-sig", "utf-8"):
        try:
            return RawExtraction(pages=[data.decode(encoding)], encoding=encoding)
        except UnicodeDecodeError:
            continue

    try:
        return RawExtraction(pages=[data.decode("cp1252")], encoding="cp1252")
    except UnicodeDecodeError as exc:
        raise ExtractionError("Could not decode text file (unknown encoding).") from exc


def _clean_meta(value: object) -> Optional[str]:
    """Turn a PDF metadata value into a trimmed string, or None if blank."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None
