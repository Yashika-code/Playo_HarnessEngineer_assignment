# Submission Checklist

## Pre-Submission

- [x] All mandatory features implemented
- [x] Backend compiled and syntax-checked
- [x] Frontend TypeScript diagnostics clean
- [x] Docker Compose configuration included
- [x] Sample input documents in `samples/input/`
- [x] Sample exported outputs in `samples/output/`
- [x] README with setup, architecture, and assumptions
- [x] `.env.example` template
- [x] `.gitignore` configured
- [x] AI tools disclosure noted

## Mandatory Features Implemented

- [x] **1. Upload one or more documents**
  - Location: `POST /documents/upload` in [backend/app/api.py](backend/app/api.py#L38)
  - Frontend: [frontend/src/App.tsx](frontend/src/App.tsx#L46) UploadView

- [x] **2. Save document metadata and job details in PostgreSQL**
  - Location: [backend/app/models.py](backend/app/models.py#L8) DocumentJob table
  - Service: [backend/app/services/documents.py](backend/app/services/documents.py#L34)

- [x] **3. Create a background processing job using Celery**
  - Location: [backend/app/workers/tasks.py](backend/app/workers/tasks.py#L44)
  - Triggered from: [backend/app/api.py](backend/app/api.py#L55) upload endpoint

- [x] **4. Use Redis Pub/Sub to publish processing progress events**
  - Location: [backend/app/services/progress.py](backend/app/services/progress.py)
  - Published in: [backend/app/workers/tasks.py](backend/app/workers/tasks.py#L65)

- [x] **5. Display job states clearly (Queued, Processing, Completed, Failed)**
  - States in DB: [backend/app/models.py](backend/app/models.py#L14)
  - Frontend display: [frontend/src/App.tsx](frontend/src/App.tsx#L139) status classes

- [x] **6. Show live or near-real-time progress in frontend**
  - SSE endpoint: `GET /documents/{id}/events` in [backend/app/api.py](backend/app/api.py#L66)
  - Frontend subscription: [frontend/src/api.ts](frontend/src/api.ts#L56) subscribeToProgress
  - Event display: [frontend/src/App.tsx](frontend/src/App.tsx#L189) DocumentDetailView

- [x] **7. Implement dashboard with search, filter by status, sorting**
  - Endpoint: `GET /documents` in [backend/app/api.py](backend/app/api.py#L59)
  - Frontend: [frontend/src/App.tsx](frontend/src/App.tsx#L109) DashboardView

- [x] **8. Document detail page for review and editing**
  - Endpoint: `GET /documents/{id}` in [backend/app/api.py](backend/app/api.py#L63)
  - Frontend edit: [frontend/src/App.tsx](frontend/src/App.tsx#L195) textarea editing

- [x] **9. Allow finalization of reviewed output**
  - Endpoint: `POST /documents/{id}/finalize` in [backend/app/api.py](backend/app/api.py#L86)
  - Frontend: [frontend/src/App.tsx](frontend/src/App.tsx#L207) finalize button

- [x] **10. Support retry for failed jobs**
  - Endpoint: `POST /documents/{id}/retry` in [backend/app/api.py](backend/app/api.py#L93)
  - Frontend: [frontend/src/App.tsx](frontend/src/App.tsx#L210) retry button

- [x] **11. Export finalized records as JSON and CSV**
  - Endpoint: `GET /documents/{id}/export?format=json|csv` in [backend/app/api.py](backend/app/api.py#L100)
  - Frontend links: [frontend/src/App.tsx](frontend/src/App.tsx#L213-L214)

## Demo Video Script (3-5 minutes)

1. **Start & Upload** (0:00-0:30)
   - Open http://localhost:5173
   - Show the upload hero screen
   - Select 1-2 sample documents and click "Upload and process"
   - Verify redirect to detail page

2. **Live Progress Tracking** (0:30-1:30)
   - Watch the progress bar fill from 0% to 100%
   - Show the live events sidebar updating in real-time
   - Point out Redis Pub/Sub events being displayed (job_started, parsing_started, extraction_started, etc.)
   - Note the status changing from "queued" → "processing" → "completed"

3. **Dashboard & Filtering** (1:30-2:15)
   - Navigate to /dashboard
   - Show the document list with all uploaded files
   - Demonstrate search by filename
   - Filter by status (completed, processing, etc.)
   - Sort by different columns (created_at, progress_percent, etc.)
   - Click through to a document detail

4. **Review & Finalize** (2:15-3:15)
   - On detail page, show the extracted JSON data
   - Edit some fields in the textarea (e.g., change title or keywords)
   - Click "Save review" to persist changes
   - Click "Finalize" to lock the document
   - Show status change to "finalized"

5. **Export & Retry** (3:15-4:00)
   - Click "Export JSON" to download the finalized record
   - Click "Export CSV" to download as CSV
   - (Optional) Upload a document, force a retry by manually failing it in the database or via a separate action
   - Show retry functionality re-queuing and processing again

6. **Architecture Summary** (4:00-4:30)
   - Briefly show the docker-compose setup
   - Mention: FastAPI backend, Celery worker, Redis for Pub/Sub and broker, PostgreSQL for storage
   - Highlight: no blocking processing in the request-response cycle

## Deliverables

- [x] Full source code in GitHub repository
- [x] README.md with all required sections
- [ ] 3-5 minute demo video (to be recorded and added to repository)
- [x] Sample files (in `samples/` folder)
- [x] Sample exported outputs (in `samples/output/` folder)
- [x] Clear note on AI tools usage (in README)

## After Recording Demo

1. Add demo video link to README (e.g., as a YouTube link or GitHub release)
2. Commit all code with a clear message
3. Push to GitHub
4. Verify repository is public and accessible
5. Submit repository link
