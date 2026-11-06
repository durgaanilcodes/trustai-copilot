import hashlib

import pytest

from trustai.exceptions import ExtractionError, FileTooLargeError, UnsupportedFileTypeError
from trustai.ingestion import ingest_bytes

from conftest import make_pdf

LONG_TEXT = "Employees must complete security training every year."


def test_txt_utf8_ingested(settings):
    data = LONG_TEXT.encode("utf-8")
    doc = ingest_bytes("policy.txt", data, settings)
    assert doc.metadata.file_type == "txt"
    assert doc.metadata.page_count == 1
    assert doc.pages[0].page_number == 1
    assert doc.full_text == LONG_TEXT
    assert doc.metadata.sha256 == hashlib.sha256(data).hexdigest()
    assert doc.metadata.word_count == 7
    assert doc.metadata.encoding == "utf-8-sig"  # utf-8-sig decodes plain UTF-8 too


def test_txt_cp1252_fallback(settings):
    data = "Caf\xe9 policy: refunds within thirty days.".encode("cp1252")
    doc = ingest_bytes("old.txt", data, settings)
    assert "Café" in doc.full_text
    assert doc.metadata.encoding == "cp1252"


def test_txt_utf16_with_bom(settings):
    data = LONG_TEXT.encode("utf-16")  # includes BOM
    doc = ingest_bytes("u16.txt", data, settings)
    assert doc.full_text == LONG_TEXT
    assert doc.metadata.encoding == "utf-16"


def test_binary_masquerading_as_txt_rejected(settings):
    with pytest.raises(ExtractionError):
        ingest_bytes("fake.txt", b"abc\x00\x01\x02def" * 10, settings)


def test_pdf_pages_and_text(settings):
    pdf = make_pdf(["First page about leave policy.", "Second page about expenses rules."])
    doc = ingest_bytes("handbook.pdf", pdf, settings)
    assert doc.metadata.file_type == "pdf"
    assert doc.metadata.page_count == 2
    assert [p.page_number for p in doc.pages] == [1, 2]
    assert "leave policy" in doc.pages[0].text
    assert "expenses rules" in doc.pages[1].text
    assert doc.metadata.empty_pages == ()


def test_pdf_empty_page_recorded(settings):
    pdf = make_pdf(["Page one has enough words to pass.", ""])
    doc = ingest_bytes("gap.pdf", pdf, settings)
    assert doc.metadata.empty_pages == (2,)


def test_image_only_pdf_rejected_with_clear_message(settings):
    pdf = make_pdf(["", ""])
    with pytest.raises(ExtractionError, match="No extractable text"):
        ingest_bytes("scan.pdf", pdf, settings)


def test_corrupt_pdf_rejected(settings):
    broken = b"%PDF-1.4\n this is not a real pdf structure at all"
    with pytest.raises(ExtractionError):
        ingest_bytes("broken.pdf", broken, settings)


def test_pdf_page_limit_enforced(settings):
    pdf = make_pdf([f"Page number {i} with some text." for i in range(settings.max_pdf_pages + 1)])
    with pytest.raises(ExtractionError, match="limit"):
        ingest_bytes("big.pdf", pdf, settings)


def test_unsupported_type_rejected(settings):
    with pytest.raises(UnsupportedFileTypeError):
        ingest_bytes("data.exe", b"MZ" + b"x" * 50, settings)


def test_too_large_rejected(settings):
    with pytest.raises(FileTooLargeError):
        ingest_bytes("huge.txt", b"a" * (settings.max_upload_bytes + 1), settings)


def test_path_in_filename_is_stripped(settings):
    doc = ingest_bytes("../../evil/policy.txt", LONG_TEXT.encode(), settings)
    assert doc.metadata.filename == "policy.txt"


def test_too_little_text_rejected(settings):
    with pytest.raises(ExtractionError):
        ingest_bytes("tiny.txt", b"hi", settings)
