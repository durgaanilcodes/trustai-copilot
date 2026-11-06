"""Custom exceptions.

Using our own exception types (instead of bare ValueError) lets the API layer
map each failure to the right HTTP status code, and lets tests assert on the
exact failure.
"""

from __future__ import annotations


class TrustAIError(Exception):
    """Base class for all TrustAI errors."""


class UnsupportedFileTypeError(TrustAIError):
    """The uploaded file type is not supported (only PDF and TXT)."""


class FileTooLargeError(TrustAIError):
    """The uploaded file exceeds the configured size limit."""


class EmptyFileError(TrustAIError):
    """The uploaded file has zero bytes."""


class ExtractionError(TrustAIError):
    """Text could not be extracted (corrupt, encrypted, or image-only file)."""


class DocumentNotFoundError(TrustAIError):
    """No stored document exists for the requested id."""
