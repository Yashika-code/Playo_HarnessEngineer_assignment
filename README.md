# Async Document Processing Workflow

Full-stack document workflow system with a React frontend, FastAPI backend, PostgreSQL persistence, Celery workers, and Redis Pub/Sub progress updates.

## Architecture

- React + TypeScript frontend for upload, dashboard, detail review, retry, finalize, and export.
- FastAPI backend for document CRUD, workflow actions, and SSE progress streaming.
- PostgreSQL for document/job state and processed output.
- Celery for asynchronous document processing.
- Redis as Celery broker and Pub/Sub channel for worker progress events.
- Local file storage for uploaded documents.

## Quick Start (Docker)

The easiest way to run the full stack:

```bash
docker compose up
```

Then open http://localhost:5173 in your browser.

## Run Locally (Without Docker)

1. Start PostgreSQL and Redis (install locally or use Docker for just these):

```bash
docker compose up -d postgres redis
```

2. Backend (terminal 1):

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

3. Worker (terminal 2):

```bash
cd backend
.venv\Scripts\activate
celery -A app.workers.celery_app.celery_app worker --loglevel=info --pool=solo
```

4. Frontend (terminal 3):

```bash
cd frontend
npm install
npm run dev
```

API will be at http://localhost:8000, frontend at http://localhost:5173.

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string.
- `REDIS_URL` - Redis connection string used by Celery and Pub/Sub.
- `STORAGE_DIR` - folder where uploaded files are persisted.
- `CORS_ORIGINS` - allowed frontend origins.

## API Surface

- `POST /documents/upload`
- `GET /documents`
- `GET /documents/{id}`
- `GET /documents/{id}/events`
- `PATCH /documents/{id}`
- `POST /documents/{id}/finalize`
- `POST /documents/{id}/retry`
- `GET /documents/{id}/export?format=json|csv`

## Assumptions

- Files are stored locally rather than in S3 or another external object store.
- The processing logic is simulated but the async workflow is real.
- SSE is used for near-real-time updates from Redis Pub/Sub.

## Tradeoffs

- Text extraction is intentionally simple so the architecture stays clear.
- SSE is easier to operate than WebSockets for this assignment and is sufficient for live updates.
- CSV export is flattened for the reviewed/finalized JSON payload.

## Limitations

- No authentication layer.
- No file virus scanning or OCR.
- Large-file chunking is not implemented.

## Demo Video

A 3-5 minute walkthrough is required for submission. See [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md) for a detailed script covering:
- Upload and live progress tracking
- Dashboard search, filter, and sorting
- Document review and finalization
- Export (JSON and CSV)
- Retry functionality

Add the demo video link here after recording:

**[Demo Video Link]** *(to be added)*

## AI Tools Used

This project was built with GitHub Copilot assistance for code scaffolding, architecture design, and implementation. All code has been reviewed and validated to meet the production-quality and design criteria outlined in the assignment.
