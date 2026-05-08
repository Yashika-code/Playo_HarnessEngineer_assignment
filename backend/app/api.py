import json
import time
from typing import Generator
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, FastAPI, File, HTTPException, Query, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.schemas import DocumentDetail, DocumentSummary, FinalizeResponse, RetryResponse, ReviewPayload, UploadResponse
from app.services.documents import create_documents, export_document, finalize_document, get_document, list_documents, retry_document, update_review
from app.services.progress import publish_progress
from app.services.storage import build_storage_path
from app.workers.tasks import process_document

settings = get_settings()
router = APIRouter()


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@router.post("/documents/upload", response_model=UploadResponse)
def upload_documents(files: list[UploadFile] = File(...), session: Session = Depends(get_session)):
    stored_files = []
    for upload in files:
        stored_filename, storage_path = build_storage_path(settings.storage_dir, upload.filename)
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        content = upload.file.read()
        storage_path.write_bytes(content)
        stored_files.append((upload.filename, stored_filename, storage_path, len(content), upload.content_type or "application/octet-stream"))

    created = create_documents(session, stored_files)
    session.commit()

    for document in created:
        process_document.delay(str(document.id))
        publish_progress(document.id, "job_queued", document.status, document.progress_percent, document.progress_step, "Processing job queued")

    return UploadResponse(created=[DocumentSummary.model_validate(document) for document in created])


@router.get("/documents", response_model=list[DocumentSummary])
def get_documents(query: str | None = None, status: str | None = None, sort_by: str = "created_at", sort_order: str = "desc", session: Session = Depends(get_session)):
    documents = list_documents(session, query, status, sort_by, sort_order)
    return [DocumentSummary.model_validate(document) for document in documents]


@router.get("/documents/{document_id}", response_model=DocumentDetail)
def document_detail(document_id: UUID, session: Session = Depends(get_session)):
    try:
        document = get_document(session, document_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentDetail.model_validate(document)


@router.get("/documents/{document_id}/events")
def document_events(document_id: UUID):
    import redis

    client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    pubsub = client.pubsub()
    pubsub.subscribe(f"document:{document_id}")

    def event_stream():
        yield f"event: connected\ndata: {json.dumps({'document_id': str(document_id), 'event': 'connected'})}\n\n"
        try:
            while True:
                message = pubsub.get_message(timeout=1.0)
                if message and message.get("type") == "message":
                    yield f"data: {message['data']}\n\n"
                time.sleep(0.5)
        finally:
            pubsub.close()
            client.close()

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.patch("/documents/{document_id}", response_model=DocumentDetail)
def update_document(document_id: UUID, payload: ReviewPayload, session: Session = Depends(get_session)):
    try:
        document = update_review(session, document_id, payload.reviewed_data)
        session.commit()
        return DocumentDetail.model_validate(document)
    except KeyError:
        raise HTTPException(status_code=404, detail="Document not found")


@router.post("/documents/{document_id}/finalize", response_model=FinalizeResponse)
def finalize(document_id: UUID, session: Session = Depends(get_session)):
    try:
        finalize_document(session, document_id)
        session.commit()
        return FinalizeResponse(status="finalized")
    except KeyError:
        raise HTTPException(status_code=404, detail="Document not found")


@router.post("/documents/{document_id}/retry", response_model=RetryResponse)
def retry(document_id: UUID, session: Session = Depends(get_session)):
    try:
        document = retry_document(session, document_id)
        session.commit()
        process_document.delay(str(document.id))
        return RetryResponse(status="queued")
    except KeyError:
        raise HTTPException(status_code=404, detail="Document not found")


@router.get("/documents/{document_id}/export")
def export(document_id: UUID, format: str = Query(default="json", pattern="^(json|csv)$"), session: Session = Depends(get_session)):
    try:
        document = get_document(session, document_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Document not found")

    content_type, content = export_document(document, format)
    filename = f"document-{document.id}.{format}"
    return Response(content=content, media_type=content_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})


def create_app() -> FastAPI:
    init_db()
    app = FastAPI(title="Async Document Workflow")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
