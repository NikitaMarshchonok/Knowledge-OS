# B2B AI Knowledge Platform Foundation

This repository is a production-style monorepo foundation for a B2B AI knowledge platform. It includes:

- `backend`: FastAPI + SQLAlchemy + Alembic
- `frontend`: Next.js (TypeScript)
- `infrastructure`: Docker Compose with Postgres, Qdrant, backend, frontend

## Product scope in this step

Implemented:

- Document upload + parsing + chunking pipeline
- Embedding + vector indexing into Qdrant
- Retrieval v1 API with project-scoped filtered vector search
- Retrieval debug UI on project details page

Not implemented intentionally:

- Chat
- LLM answer generation
- Reranking
- Hybrid retrieval

## Document lifecycle

Current status lifecycle:

- `uploaded` -> file persisted and processing scheduled
- `processing` -> parser + chunking pipeline running
- `processed` -> text extracted and chunks stored in PostgreSQL
- `indexed` -> chunk vectors upserted into Qdrant
- `failed` -> processing failure persisted in `processing_error`

## Backend API routes

Projects and uploads:

- `GET /health`
- `GET /projects`
- `POST /projects`
- `GET /projects/{id}`
- `POST /projects/{id}/documents/upload`
- `GET /projects/{id}/documents`

Documents and indexing:

- `GET /documents/{id}`
- `GET /documents/{id}/chunks?offset=0&limit=100`
- `POST /documents/{id}/index`
- `POST /documents/{id}/reindex`
- `GET /documents/{id}/index-status`

Retrieval v1:

- `POST /search`

Request body:

```json
{
  "query": "what does the pricing policy say",
  "project_id": "<uuid>",
  "top_k": 8,
  "document_ids": ["<uuid>"],
  "mime_types": ["application/pdf"]
}
```

Response body:

- `query`
- `top_k`
- `total_results`
- `results[]` where each item has:
  - `chunk_id`
  - `document_id`
  - `source_filename`
  - `chunk_index`
  - `content`
  - `score`
  - `char_start`
  - `char_end`
  - `mime_type`

## Retrieval v1 architecture

- `app/services/retrieval.py` orchestrates retrieval logic
- Embeddings are generated through existing provider abstraction (`app/services/embeddings`)
- Qdrant search uses extended vector store service (`app/services/vector_store/qdrant_service.py`)
- API route remains thin in `app/api/routes/search.py`

Retrieval flow:

1. Validate request and project scope
2. Embed query with the configured embedding provider
3. Query Qdrant with metadata filters:
   - required: `project_id`
   - optional: `document_ids`, `mime_types`
4. Enrich hits from PostgreSQL for stable content/source fields
5. Return top-k results

## Qdrant payload metadata

Each indexed chunk stores:

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

Indexing/retrieval dependencies:

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
