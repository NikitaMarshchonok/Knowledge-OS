# B2B AI Knowledge Platform Foundation

This repository is a production-style monorepo foundation for a B2B AI knowledge platform. It includes:

- `backend`: FastAPI + SQLAlchemy + Alembic
- `frontend`: Next.js (TypeScript)
- `infrastructure`: Docker Compose with Postgres, Qdrant, backend, frontend

## Product scope in this step

Implemented:

- Projects and document management foundation
- File upload pipeline (local storage)
- Clean API contracts and frontend API client
- Project list/detail UI with upload flow and document status table

Not implemented intentionally:

- Chat
- Embeddings
- Indexing pipelines
- Retrieval orchestration

## Monorepo structure

- `backend/app`: FastAPI application modules
- `backend/alembic`: DB migrations
- `frontend/src`: Next.js app code
- `docker-compose.yml`: local infrastructure stack

## Backend API routes

- `GET /health`
- `GET /projects`
- `POST /projects`
- `GET /projects/{id}`
- `POST /projects/{id}/documents/upload`
- `GET /projects/{id}/documents`

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

- SQLAlchemy models are in `backend/app/models`
- Initial migration is `backend/alembic/versions/0001_initial.py`
- On container start, backend runs `alembic upgrade head` automatically

## Notes for next milestones

- Add auth and workspace membership model
- Add async document processing worker
- Add embeddings + vector indexing (Qdrant)
- Add citation-aware retrieval and chat APIs
