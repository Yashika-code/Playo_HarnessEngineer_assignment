import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import redis

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.models import DocumentJob
from app.services.progress import publish_progress
from app.workers.celery_app import celery_app

settings = get_settings()


def _load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return f"Binary or unsupported file content for {path.name}"


def _generate_structured_data(document: DocumentJob, text: str) -> dict[str, object]:
    words = [word.strip(".,;:!?()[]{}\n\r\t").lower() for word in text.split()]
    keywords = sorted({word for word in words if len(word) > 4})[:8]
    return {
        "title": document.original_filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title(),
        "category": "document",
        "summary": text[:240] if text else f"Processed file {document.original_filename}",
        "keywords": keywords,
        "status": "processed",
        "metadata": {
            "filename": document.original_filename,
            "file_type": document.file_type,
            "file_size": document.file_size,
        },
    }


@celery_app.task(bind=True, name="process_document")
def process_document(self, document_id: str) -> dict[str, object]:
    init_db()
    session = SessionLocal()
    redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        doc_uuid = UUID(document_id)
        document = session.get(DocumentJob, doc_uuid)
        if document is None:
            raise ValueError(f"Document {document_id} not found")

        document.status = "processing"
        document.progress_step = "document_received"
        document.progress_percent = 5
        document.updated_at = datetime.now(timezone.utc)
        session.flush()
        publish_progress(document.id, "job_started", document.status, document.progress_percent, document.progress_step, "Document received")
        time.sleep(0.2)

        document.progress_step = "parsing_started"
        document.progress_percent = 20
        session.flush()
        publish_progress(document.id, "document_parsing_started", document.status, document.progress_percent, document.progress_step, "Parsing started")
        time.sleep(0.4)

        text = _load_text(Path(document.storage_path))
        document.progress_step = "parsing_completed"
        document.progress_percent = 45
        session.flush()
        publish_progress(document.id, "document_parsing_completed", document.status, document.progress_percent, document.progress_step, "Parsing completed")
        time.sleep(0.2)

        document.progress_step = "extraction_started"
        document.progress_percent = 60
        session.flush()
        publish_progress(document.id, "field_extraction_started", document.status, document.progress_percent, document.progress_step, "Extraction started")
        time.sleep(0.4)

        extracted = _generate_structured_data(document, text)
        document.extracted_data = extracted
        document.reviewed_data = document.reviewed_data or extracted
        document.progress_step = "extraction_completed"
        document.progress_percent = 80
        session.flush()
        publish_progress(document.id, "field_extraction_completed", document.status, document.progress_percent, document.progress_step, "Extraction completed", extracted)
        time.sleep(0.2)

        document.finalized_data = document.finalized_data or extracted
        document.status = "completed"
        document.progress_step = "final_result_stored"
        document.progress_percent = 100
        document.completed_at = datetime.now(timezone.utc)
        session.flush()
        publish_progress(document.id, "final_result_stored", document.status, document.progress_percent, document.progress_step, "Final result stored", extracted)
        publish_progress(document.id, "job_completed", document.status, document.progress_percent, document.progress_step, "Job completed", extracted)
        session.commit()
        return extracted
    except Exception as exc:
        session.rollback()
        try:
            document = session.get(DocumentJob, UUID(document_id))
            if document is not None:
                document.status = "failed"
                document.error_message = str(exc)
                document.progress_step = "job_failed"
                document.updated_at = datetime.now(timezone.utc)
                session.commit()
                publish_progress(document.id, "job_failed", document.status, document.progress_percent, document.progress_step, str(exc))
        except Exception:
            session.rollback()
        raise
    finally:
        redis_client.close()
        session.close()
