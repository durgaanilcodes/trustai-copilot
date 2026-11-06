"""API tests. Skipped automatically if FastAPI/httpx are not installed."""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from conftest import make_pdf  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TRUSTAI_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("TRUSTAI_MAX_UPLOAD_MB", "1")
    from trustai.api.main import app

    return TestClient(app)


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_upload_txt_then_fetch_and_delete(client):
    body = b"Expense claims must be filed within thirty days."
    resp = client.post("/documents", files={"file": ("expenses.txt", body, "text/plain")})
    assert resp.status_code == 201
    doc_id = resp.json()["document_id"]

    assert client.get(f"/documents/{doc_id}").json()["pages"][0]["page_number"] == 1
    assert len(client.get("/documents").json()) == 1
    assert client.delete(f"/documents/{doc_id}").status_code == 200
    assert client.get(f"/documents/{doc_id}").status_code == 404


def test_upload_pdf(client):
    pdf = make_pdf(["Quarterly security review checklist items."])
    resp = client.post("/documents", files={"file": ("q.pdf", pdf, "application/pdf")})
    assert resp.status_code == 201
    assert resp.json()["metadata"]["page_count"] == 1


def test_wrong_type_415(client):
    resp = client.post("/documents", files={"file": ("a.exe", b"MZ" + b"x" * 40, "application/x-msdownload")})
    assert resp.status_code == 415


def test_empty_file_422(client):
    resp = client.post("/documents", files={"file": ("a.txt", b"", "text/plain")})
    assert resp.status_code == 422


def test_too_large_413(client):
    resp = client.post("/documents", files={"file": ("a.txt", b"a" * (1024 * 1024 + 5), "text/plain")})
    assert resp.status_code == 413


def test_missing_document_404(client):
    assert client.get("/documents/00000000-0000-0000-0000-000000000000").status_code == 404
    assert client.get("/documents/not-a-uuid").status_code == 404
