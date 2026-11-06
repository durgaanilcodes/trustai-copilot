"""Upload validation: check the file BEFORE spending effort parsing it.

Security note: never trust the filename or the declared content-type from a
client. We check the extension, the size, and the file's real leading bytes.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath, PureWindowsPath

from trustai.exceptions import EmptyFileError, FileTooLargeError, UnsupportedFileTypeError

SUPPORTED_TYPES = {".pdf": "pdf", ".txt": "txt"}
_PDF_MAGIC = b"%PDF-"


def sanitize_filename(filename: str) -> str:
    """Return a safe display name: no directories, no control characters.

    Handles both Windows (`C:\\x\\a.pdf`) and POSIX (`../../a.pdf`) paths so a
    malicious name cannot point outside the upload folder.
    """
    name = PureWindowsPath(filename).name
    name = PurePosixPath(name).name
    name = re.sub(r"[\x00-\x1f\x7f]", "", name).strip()
    return name or "unnamed"


def detect_file_type(filename: str) -> str:
    """Map a filename to 'pdf' or 'txt', or raise UnsupportedFileTypeError."""
    suffix = PurePosixPath(sanitize_filename(filename)).suffix.lower()
    if suffix not in SUPPORTED_TYPES:
        raise UnsupportedFileTypeError(
            f"Unsupported file type {suffix or '(none)'!r}. Only .pdf and .txt are allowed."
        )
    return SUPPORTED_TYPES[suffix]


def validate_upload(filename: str, data: bytes, max_bytes: int) -> str:
    """Validate an upload and return its file type ('pdf' or 'txt').

    Raises:
        UnsupportedFileTypeError: wrong extension, or a .pdf that is not a PDF.
        EmptyFileError: zero bytes.
        FileTooLargeError: larger than `max_bytes`.
    """
    file_type = detect_file_type(filename)
    if len(data) == 0:
        raise EmptyFileError("The uploaded file is empty.")
    if len(data) > max_bytes:
        raise FileTooLargeError(
            f"File is {len(data) / 1_048_576:.1f} MB; the limit is {max_bytes / 1_048_576:.0f} MB."
        )
    if file_type == "pdf" and not data.lstrip()[:5].startswith(_PDF_MAGIC):
        raise UnsupportedFileTypeError("File has a .pdf extension but is not a valid PDF.")
    return file_type
