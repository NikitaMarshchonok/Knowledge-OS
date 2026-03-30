# B2B AI Knowledge Platform Foundation

This repository is a production-style monorepo foundation for a B2B AI knowledge platform. It includes:

- `backend`: FastAPI + SQLAlchemy + Alembic
- `frontend`: Next.js (TypeScript)
- `infrastructure`: Docker Compose with Postgres, Qdrant, backend, frontend

## Product scope in this step

Implemented:

- Document upload + parsing + chunking pipeline
- Embedding + vector indexing into Qdrant
- Retrieval + reranking v1 API (`POST /search`)
- Retrieval debug UI on project details page with score diagnostics

Not implemented intentionally:

- Chat
- LLM answer generation
- Citation rendering UI
- Hybrid retrieval
- Worker queue changes

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

Search (retrieval + reranking):

- `POST /search`

## `/search` contract

Request body:

```json
{
  "query": "what does the refund policy say",
  "project_id": "<uuid>",
  "top_k": 8,
  "document_ids": ["<uuid>"],
  "mime_types": ["application/pdf"],
  "debug": false
}
```

Response fields:

- `query`
- `top_k`
- `total_results`
- `results[]`:
  - `chunk_id`
  - `document_id`
  - `source_filename`
  - `chunk_index`
  - `content`
  - `original_vector_score`
  - `rerank_score`
  - `final_rank`
  - `char_start`
  - `char_end`
  - `mime_type`
- optional `debug`:
  - `pre_rerank_chunk_ids`
  - `post_rerank_chunk_ids`

## Retrieval + reranking pipeline

Pipeline order:

1. Embed query
2. Search Qdrant by vector similarity with required `project_id` filter
3. Fetch top N candidates (`RERANK_TOP_N`, configurable)
4. Enrich with PostgreSQL chunk/document data
5. Rerank candidates when enabled
6. Return final top K

Service structure:

- `app/services/search_pipeline.py`
- `app/services/reranking/base.py`
- `app/services/reranking/factory.py`
- `app/services/reranking/local_reranker.py`
- `app/services/vector_store/qdrant_service.py`

## Configuration

Important backend env vars:

- `QDRANT_URL`
- `QDRANT_COLLECTION_NAME`
- `EMBEDDING_PROVIDER`
- `EMBEDDING_MODEL_NAME`
- `EMBEDDING_DIMENSION`
- `EMBEDDING_BATCH_SIZE`
- `RERANKING_ENABLED`
- `RERANK_TOP_N`
- `RERANK_PROVIDER`
- `RERANK_MODEL_NAME`

Defaults use local embedding-similarity reranking provider.

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
