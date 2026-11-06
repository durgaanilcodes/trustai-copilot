"""Shared test helpers.

`make_pdf` builds a tiny valid PDF by hand so tests need no extra libraries
(and no binary fixture files in git).
"""

from __future__ import annotations

import pytest

from trustai.config import Settings


def make_pdf(pages: list[str]) -> bytes:
    """Build a minimal PDF with one line of Helvetica text per page.

    An empty string produces a page with no text (like a blank or scanned page).
    """
    objects: list[bytes] = []
    n = len(pages)
    # Object numbering: 1=catalog, 2=pages, 3=font, then (page, content) pairs.
    kids = " ".join(f"{4 + 2 * i} 0 R" for i in range(n))
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {n} >>".encode())
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for i, text in enumerate(pages):
        content_obj = 5 + 2 * i
        safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 12 Tf 72 720 Td ({safe}) Tj ET".encode("latin-1") if text else b""
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_obj} 0 R >>"
            ).encode()
        )
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")

    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for num, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{num} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n"
    ).encode()
    return bytes(out)


@pytest.fixture
def settings(tmp_path) -> Settings:
    """Settings pointing at a temporary upload folder with small limits."""
    return Settings(
        env="test",
        log_level="WARNING",
        upload_dir=tmp_path / "uploads",
        max_upload_bytes=1024 * 1024,  # 1 MB
        max_pdf_pages=10,
        min_text_chars=20,
    )
