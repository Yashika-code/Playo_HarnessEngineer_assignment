# API Reference

## Base URL
- Local: `http://localhost:8000`
- Production: Configure via `DATABASE_URL`, `REDIS_URL`, `CORS_ORIGINS`

## Endpoints

### Upload

**POST** `/documents/upload`

Upload one or more documents and queue them for processing.

```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "files=@sample.txt" \
  -F "files=@another.txt"
```

**Response** (201):
```json
{
  "created": [
    {
      "id": "uuid-1",
      "original_filename": "sample.txt",
      "file_type": "text/plain",
      "file_size": 1024,
      "status": "queued",
      "progress_step": "job_queued",
      "progress_percent": 0,
      "created_at": "2026-05-08T12:00:00Z",
      "updated_at": "2026-05-08T12:00:00Z",
      "finalized_at": null
    }
  ]
}
```

---

### List Documents

**GET** `/documents?query=foo&status=processing&sort_by=created_at&sort_order=desc`

List all documents with optional filtering and sorting.

**Query Parameters:**
- `query` (optional): Search by filename (case-insensitive substring match)
- `status` (optional): Filter by status (`queued`, `processing`, `completed`, `failed`, `finalized`)
- `sort_by` (optional): Sort column (`created_at`, `updated_at`, `status`, `progress_percent`, `filename`) - default: `created_at`
- `sort_order` (optional): Sort direction (`asc`, `desc`) - default: `desc`

**Response** (200):
```json
[
  {
    "id": "uuid-1",
    "original_filename": "sample.txt",
    "file_type": "text/plain",
    "file_size": 1024,
    "status": "completed",
    "progress_step": "final_result_stored",
    "progress_percent": 100,
    "created_at": "2026-05-08T12:00:00Z",
    "updated_at": "2026-05-08T12:02:00Z",
    "finalized_at": null
  }
]
```

---

### Get Document Detail

**GET** `/documents/{document_id}`

Get full details including extracted, reviewed, and finalized data.

**Response** (200):
```json
{
  "id": "uuid-1",
  "original_filename": "sample.txt",
  "file_type": "text/plain",
  "file_size": 1024,
  "status": "completed",
  "progress_step": "final_result_stored",
  "progress_percent": 100,
  "storage_path": "/app/storage/uploads/abc123.txt",
  "extracted_data": {
    "title": "Sample",
    "category": "document",
    "summary": "Sample content...",
    "keywords": ["sample", "document"],
    "status": "processed",
    "metadata": { "filename": "sample.txt", "file_type": "text/plain", "file_size": 1024 }
  },
  "reviewed_data": null,
  "finalized_data": null,
  "error_message": null,
  "created_at": "2026-05-08T12:00:00Z",
  "updated_at": "2026-05-08T12:02:00Z",
  "completed_at": "2026-05-08T12:02:00Z",
  "finalized_at": null
}
```

---

### Stream Progress Events

**GET** `/documents/{document_id}/events`

Server-Sent Events stream of progress updates from the worker.

**Response** (200, streaming):
```
event: connected
data: {"document_id": "uuid-1", "event": "connected"}

data: {"document_id": "uuid-1", "event": "job_started", "status": "processing", "progress_percent": 5, "progress_step": "document_received", "message": "Document received", "payload": {}}

data: {"document_id": "uuid-1", "event": "document_parsing_started", "status": "processing", "progress_percent": 20, "progress_step": "parsing_started", "message": "Parsing started", "payload": {}}

...
```

---

### Update Document (Save Review)

**PATCH** `/documents/{document_id}`

Save reviewed/edited data for a document.

**Request Body:**
```json
{
  "reviewed_data": {
    "title": "Edited Title",
    "category": "custom_category",
    "summary": "Custom summary",
    "keywords": ["custom", "tags"]
  }
}
```

**Response** (200): Same as GET detail endpoint with `reviewed_data` populated.

---

### Finalize Document

**POST** `/documents/{document_id}/finalize`

Lock the document as finalized (uses reviewed_data if available, otherwise extracted_data).

**Request Body:** (empty)

**Response** (200):
```json
{
  "status": "finalized"
}
```

Document status changes to `finalized`, and `finalized_at` timestamp is set.

---

### Retry Failed Document

**POST** `/documents/{document_id}/retry`

Re-queue a failed document for processing.

**Request Body:** (empty)

**Response** (200):
```json
{
  "status": "queued"
}
```

Document status resets to `queued`, error is cleared, and a new Celery task is created.

---

### Export Document

**GET** `/documents/{document_id}/export?format=json`

Export finalized (or reviewed or extracted) data as JSON or CSV.

**Query Parameters:**
- `format` (required): `json` or `csv`

**Response** (200):
- Content-Type: `application/json` or `text/csv`
- Content-Disposition: `attachment; filename="document-{id}.json"` or `.csv`

**JSON Output:**
```json
{
  "title": "Finalized Title",
  "category": "document",
  "summary": "...",
  "keywords": [...],
  "status": "processed",
  "metadata": {...}
}
```

**CSV Output:**
```
field,value
title,Finalized Title
category,document
summary,...
keywords,"keyword1, keyword2"
status,processed
```

---

### Health Check

**GET** `/health`

Simple health check endpoint.

**Response** (200):
```json
{
  "status": "ok"
}
```

---

## Error Responses

All errors return appropriate HTTP status codes:

- **400 Bad Request**: Malformed input
- **404 Not Found**: Document does not exist
- **422 Unprocessable Entity**: Validation error in request body
- **500 Internal Server Error**: Server-side error (check logs)

**Error Response Format:**
```json
{
  "detail": "Error message here"
}
```

---

## Processing Workflow

1. **Upload** → `POST /documents/upload` → Status: `queued`
2. **Celery picks up job** → Status: `processing`, progress_step: `document_received`
3. **Worker emits events** → `GET /documents/{id}/events` receives real-time updates
4. **Processing stages**:
   - `document_received` (5%)
   - `parsing_started` (20%)
   - `parsing_completed` (45%)
   - `extraction_started` (60%)
   - `extraction_completed` (80%)
   - `final_result_stored` (100%)
5. **Job completes** → Status: `completed`
6. **User reviews** → `PATCH /documents/{id}` to save changes
7. **User finalizes** → `POST /documents/{id}/finalize` → Status: `finalized`
8. **Export** → `GET /documents/{id}/export?format=json|csv`

If processing fails at any step:
- Status → `failed`
- error_message populated
- User can → `POST /documents/{id}/retry`
