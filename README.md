# TrustAI — Enterprise Knowledge Copilot with Risk-Aware Multi-Agent RAG

A secure enterprise knowledge assistant: upload company documents, ask questions, and get
answers grounded in those documents, with citations and a risk assessment.

> **Status: Phase 1 of 7 — document ingestion only.**
> Retrieval, answer generation, agents, security scoring, evaluation and the dashboard are
> **not built yet**. This README describes the target design and clearly marks what exists today.

## Roadmap

| Phase | Scope | Status |
|------:|-------|--------|
| 1 | Project structure, config, PDF/TXT upload and text extraction | **Done** |
| 2 | Chunking, embeddings, PostgreSQL + pgvector, retrieval | Planned |
| 3 | RAG answer generation with citations and refusal | Planned |
| 4 | Multi-agent workflow, prompt-injection detection, trust scoring | Planned |
| 5 | Evaluation (Recall@K, Precision@K, faithfulness, latency, tokens) | Planned |
| 6 | Streamlit dashboard | Planned |
| 7 | Docker and deployment | Planned |

No evaluation numbers are reported yet because nothing has been evaluated yet.

## Target architecture

```
Upload -> Ingestion -> Chunk + Embed -> PostgreSQL/pgvector
                                              |
                          Retrieval (vector + keyword, rerank)
                                              |
        Research -> Context Validation -> Risk Assessment -> Response
                                              |
                              Answer + citations + risk status -> Streamlit UI
```

Design rules:

1. **Layers.** `trustai/api/` only handles HTTP; the real logic is plain Python that never imports FastAPI, so it is easy to test.
2. **Security is code, not LLM opinion.** Injection detection and trust scoring will be deterministic, explainable rules with test cases.
3. **Configuration via environment variables.** No secrets in source (see `.env.example`).

## Project structure

```
trustai/
  config.py, exceptions.py, logging_config.py
  api/          FastAPI app (Phase 1: upload endpoints)
  ingestion/    validation, extraction, cleaning, metadata   (Phase 1)
  storage/      local disk store (Phase 1) -> PostgreSQL (Phase 2)
  retrieval/ rag/ agents/ security/ evaluation/              (later phases)
frontend/       Streamlit (Phase 6)
tests/          pytest suite
data/uploads    stored uploads (git-ignored)
docs/ docker/ scripts/
```

## What Phase 1 does

- Accepts `.pdf` and `.txt` uploads and validates them (extension, size, empty file, real PDF header).
- Extracts text **per page**, so later citations can name a page.
- Cleans text (ligatures, hyphenated line breaks, whitespace).
- Records measured metadata: SHA-256 hash, size, pages, words, characters, PDF title/author/date, text encoding, empty pages.
- Stores the original file and extracted text on local disk under a random UUID.

### Known limitations

- **No OCR.** Scanned/image-only PDFs are rejected with a clear message.
- Tables and multi-column PDFs are flattened to plain text.
- TXT files count as one page, so they have no page numbers in citations.
- Password-protected PDFs are rejected.
- Local-disk storage is temporary; Phase 2 moves to PostgreSQL.

## Installation

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env               # Windows: copy .env.example .env
```

## Run

```bash
uvicorn trustai.api.main:app --reload
```

Open http://127.0.0.1:8000/docs for interactive API docs.

```bash
curl -F "file=@handbook.pdf" http://127.0.0.1:8000/documents
curl http://127.0.0.1:8000/documents
curl http://127.0.0.1:8000/documents/<document_id>
curl -X DELETE http://127.0.0.1:8000/documents/<document_id>
```

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness check |
| POST | `/documents` | Upload a PDF/TXT (201; 413 too large; 415 wrong type; 422 unreadable/empty/no text) |
| GET | `/documents` | List documents and metadata |
| GET | `/documents/{id}` | Metadata and per-page text |
| DELETE | `/documents/{id}` | Delete a document |

## Tests

```bash
pytest
```

API tests are skipped automatically if FastAPI/httpx are not installed.

## Configuration

See `.env.example`. Key settings: `TRUSTAI_UPLOAD_DIR`, `TRUSTAI_MAX_UPLOAD_MB`,
`TRUSTAI_MAX_PDF_PAGES`, `TRUSTAI_MIN_TEXT_CHARS`, `TRUSTAI_LOG_LEVEL`.

## Still to come (portfolio checklist)

Architecture diagram, screenshots, evaluation report with real results, Docker setup,
demo video outline, deployment instructions.
