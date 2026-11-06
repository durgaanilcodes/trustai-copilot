import pytest

from trustai.exceptions import EmptyFileError, FileTooLargeError, UnsupportedFileTypeError
from trustai.ingestion.validation import detect_file_type, sanitize_filename, validate_upload


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("../../etc/passwd.txt", "passwd.txt"),
        ("C:\\Users\\me\\report.pdf", "report.pdf"),
        ("normal.txt", "normal.txt"),
        ("bad\x00name.txt", "badname.txt"),
        ("", "unnamed"),
    ],
)
def test_sanitize_filename(raw, expected):
    assert sanitize_filename(raw) == expected


def test_detect_file_type_case_insensitive():
    assert detect_file_type("A.PDF") == "pdf"
    assert detect_file_type("notes.TxT") == "txt"


@pytest.mark.parametrize("name", ["malware.exe", "image.png", "noextension", "archive.pdf.zip"])
def test_unsupported_extension_rejected(name):
    with pytest.raises(UnsupportedFileTypeError):
        detect_file_type(name)


def test_empty_file_rejected():
    with pytest.raises(EmptyFileError):
        validate_upload("a.txt", b"", 1000)


def test_oversized_file_rejected():
    with pytest.raises(FileTooLargeError):
        validate_upload("a.txt", b"x" * 11, 10)


def test_fake_pdf_rejected():
    with pytest.raises(UnsupportedFileTypeError):
        validate_upload("a.pdf", b"this is plain text pretending to be a pdf", 1000)
