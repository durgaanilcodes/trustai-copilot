import pytest

from trustai.exceptions import DocumentNotFoundError
from trustai.ingestion import ingest_bytes
from trustai.storage import LocalDocumentStore

TEXT = b"Remote work is allowed up to three days per week."


def test_save_get_list_delete_roundtrip(settings):
    store = LocalDocumentStore(settings.upload_dir)
    doc = ingest_bytes("remote.txt", TEXT, settings)

    doc_id = store.save(doc, TEXT)
    assert store.list_ids() == [doc_id]

    loaded = store.get(doc_id)
    assert loaded == doc  # lossless roundtrip through JSON

    store.delete(doc_id)
    assert store.list_ids() == []
    with pytest.raises(DocumentNotFoundError):
        store.get(doc_id)


@pytest.mark.parametrize("bad_id", ["../../etc/passwd", "not-a-uuid", "", "..", "a/b"])
def test_path_traversal_ids_rejected(settings, bad_id):
    store = LocalDocumentStore(settings.upload_dir)
    with pytest.raises(DocumentNotFoundError):
        store.get(bad_id)
    with pytest.raises(DocumentNotFoundError):
        store.delete(bad_id)


def test_original_bytes_preserved(settings):
    store = LocalDocumentStore(settings.upload_dir)
    doc = ingest_bytes("remote.txt", TEXT, settings)
    doc_id = store.save(doc, TEXT)
    assert (settings.upload_dir / doc_id / "original.txt").read_bytes() == TEXT
