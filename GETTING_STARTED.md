# Getting Started (60 seconds)

## Option 1: Docker (Recommended)

```bash
git clone <repository-url>
cd assign
docker compose up
# Wait for all services to start
# Open http://localhost:5173 in your browser
```

No local Python, Node.js, PostgreSQL, or Redis setup needed.

## Option 2: Local Setup

Prerequisites: Python 3.10+, Node.js 18+, PostgreSQL 16, Redis 7

```bash
# Terminal 1: Infrastructure
docker compose up -d postgres redis

# Terminal 2: Backend
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Terminal 3: Worker
cd backend
.venv\Scripts\activate
celery -A app.workers.celery_app.celery_app worker --loglevel=info --pool=solo

# Terminal 4: Frontend
cd frontend
npm install
npm run dev
```

## Test the App

1. **Upload**: Go to http://localhost:5173 and upload a document (use files from `samples/input/`)
2. **Track**: Watch the progress bar and live events as the worker processes it
3. **Review**: Edit the extracted data and click "Save review"
4. **Finalize**: Click "Finalize" to lock the document
5. **Export**: Click "Export JSON" or "Export CSV" to download results
6. **Dashboard**: Go to /dashboard to see all documents with search, filter, and sort

## Key URLs

- Frontend: http://localhost:5173
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## What's Inside

| Folder | Purpose |
|--------|---------|
| `backend/app/` | FastAPI routes, models, services |
| `backend/app/workers/` | Celery task definitions |
| `frontend/src/` | React components, API client, types |
| `samples/` | Example input documents and exported outputs |
| `docker-compose.yml` | Full stack orchestration |

## Next Steps

- See [README.md](README.md) for full architecture and API details
- See [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md) for demo script
- See [BONUS_POINTS.md](BONUS_POINTS.md) for implemented features
