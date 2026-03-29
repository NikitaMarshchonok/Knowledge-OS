# B2B AI Knowledge Platform Foundation

This repository is a production-style monorepo foundation for a B2B AI knowledge platform. It includes:

- `backend`: FastAPI + SQLAlchemy + Alembic
- `frontend`: Next.js (TypeScript)
- `infrastructure`: Docker Compose with Postgres, Qdrant, backend, frontend

## Product scope in this step

Implemented:

- Projects and document management foundation
- Local file upload + asynchronous document processing
- Chunk persistence in PostgreSQL
- Manual embedding + vector indexing pipeline into Qdrant
- Clean API contracts and frontend API client
- Project detail UI with processing/indexing status polling and index/reindex actions

Not implemented intentionally:

- Chat
- Retrieval APIs
- Reranking
- Answer generation

## Document lifecycle

Current status lifecycle:

- `uploaded` -> file persisted and processing scheduled
- `processing` -> parser + chunking pipeline running
- `processed` -> text extracted and chunks stored in PostgreSQL
- `indexed` -> chunk vectors upserted into Qdrant
- `failed` -> processing failure persisted in `processing_error`

### What “processed” means

A document is `processed` when text extraction and chunk storage completed successfully.

### What “indexed” means

A document is `indexed` when embeddings are generated for all stored chunks and upserted into Qdrant.

## Supported file types

Parser support currently includes:

- `.txt`
- `.pdf`
- `.docx`
- `.csv`
- `.xlsx`

Unsupported types fail safely with `status=failed` and a persisted `processing_error`.

## Backend API routes

Projects and uploads:

- `GET /health`
- `GET /projects`
- `POST /projects`
- `GET /projects/{id}`
- `POST /projects/{id}/documents/upload`
- `GET /projects/{id}/documents`

Document visibility:

- `GET /documents/{id}`
- `GET /documents/{id}/chunks?offset=0&limit=100`

Indexing endpoints:

- `POST /documents/{id}/index`
- `POST /documents/{id}/reindex`
- `GET /documents/{id}/index-status`

## Indexing pipeline design

Service structure:

- `app/services/embeddings/` -> provider abstraction + default provider
- `app/services/vector_store/` -> Qdrant index service
- `app/services/document_indexing.py` -> orchestration

Indexing flow:

1. Validate document state (`processed`/`indexed`) and chunk availability
2. Mark `is_indexing=true`
3. Load chunks in deterministic order (`chunk_index`)
4. Generate embeddings through provider abstraction
5. Ensure Qdrant collection exists (size checked against configured dimension)
6. Delete existing vectors for the document (reindex-safe)
7. Upsert vectors with citation-friendly payload metadata
8. Set `status=indexed`, `indexed_at`, clear indexing errors
9. On failure, clear `is_indexing` and persist `indexing_error`

Qdrant payload per chunk includes:

- `chunk_id`
- `document_id`
- `project_id`
- `chunk_index`
- `source_filename`
- `char_start`
- `char_end`
- `mime_type`

## Configuration

Important backend env vars:

- `QDRANT_URL`
- `QDRANT_COLLECTION_NAME`
- `EMBEDDING_PROVIDER`
- `EMBEDDING_MODEL_NAME`
- `EMBEDDING_DIMENSION`
- `EMBEDDING_BATCH_SIZE`
- `DEFAULT_CHUNK_SIZE`
- `DEFAULT_CHUNK_OVERLAP`

## Dependencies

Processing dependencies:

- `pypdf`
- `python-docx`
- `openpyxl`

Indexing dependencies:

- `qdrant-client`
- `fastembed`

## Local run (Docker Compose - recommended)

### 1) Start services

```bash
docker compose up --build
```

### 2) Open apps

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Qdrant: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

### 3) Stop services

```bash
docker compose down
```

To also remove persisted volumes:

```bash
docker compose down -v
```

## Local run (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Database and migrations

- `backend/alembic/versions/0001_initial.py`
- `backend/alembic/versions/0002_document_processing_pipeline.py`
- `backend/alembic/versions/0003_document_indexing_metadata.py`

## Notes for next milestones

- Add durable worker queue for processing/indexing jobs
- Add retrieval APIs using Qdrant filters
- Add citation-aware answer generation APIs
