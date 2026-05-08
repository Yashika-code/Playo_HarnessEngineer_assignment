import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from app.models import DocumentJob
from app.services.progress import publish_progress


def serialize_document(document: DocumentJob) -> dict[str, Any]:
    return {
        "id": str(document.id),
        "original_filename": document.original_filename,
        "file_type": document.file_type,
        "file_size": document.file_size,
        "status": document.status,
        "progress_step": document.progress_step,
        "progress_percent": document.progress_percent,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
        "finalized_at": document.finalized_at,
    }


def create_documents(session: Session, files: list[tuple[str, str, Path, int, str]]) -> list[DocumentJob]:
    created: list[DocumentJob] = []
    for original_filename, stored_filename, storage_path, file_size, file_type in files:
        document = DocumentJob(
            original_filename=original_filename,
            stored_filename=stored_filename,
            storage_path=str(storage_path),
            file_type=file_type,
            file_size=file_size,
            status="queued",
            progress_step="job_queued",
            progress_percent=0,
        )
        session.add(document)
        session.flush()
        publish_progress(document.id, "job_queued", document.status, document.progress_percent, document.progress_step, "Document queued")
        created.append(document)
    return created


def list_documents(session: Session, query: str | None, status: str | None, sort_by: str, sort_order: str) -> list[DocumentJob]:
    statement = select(DocumentJob)
    if query:
        like_query = f"%{query.lower()}%"
        statement = statement.where(DocumentJob.original_filename.ilike(like_query))
    if status:
        statement = statement.where(DocumentJob.status == status)
    sort_column = {
        "created_at": DocumentJob.created_at,
        "updated_at": DocumentJob.updated_at,
        "status": DocumentJob.status,
        "progress_percent": DocumentJob.progress_percent,
        "filename": DocumentJob.original_filename,
    }.get(sort_by, DocumentJob.created_at)
    statement = statement.order_by(asc(sort_column) if sort_order == "asc" else desc(sort_column))
    return list(session.scalars(statement).all())


def get_document(session: Session, document_id: UUID) -> DocumentJob:
    document = session.get(DocumentJob, document_id)
    if document is None:
        raise KeyError(str(document_id))
    return document


def update_review(session: Session, document_id: UUID, reviewed_data: dict[str, Any]) -> DocumentJob:
    document = get_document(session, document_id)
    document.reviewed_data = reviewed_data
    session.flush()
    return document


def finalize_document(session: Session, document_id: UUID) -> DocumentJob:
    document = get_document(session, document_id)
    final_payload = document.reviewed_data or document.extracted_data or {}
    document.finalized_data = final_payload
    document.status = "finalized"
    document.progress_step = "final_result_stored"
    document.progress_percent = 100
    document.finalized_at = datetime.now(timezone.utc)
    document.completed_at = document.completed_at or datetime.now(timezone.utc)
    session.flush()
    publish_progress(document.id, "job_completed", document.status, document.progress_percent, document.progress_step, "Document finalized", final_payload)
    return document


def retry_document(session: Session, document_id: UUID) -> DocumentJob:
    document = get_document(session, document_id)
    document.status = "queued"
    document.progress_step = "job_queued"
    document.progress_percent = 0
    document.error_message = None
    document.completed_at = None
    session.flush()
    publish_progress(document.id, "job_queued", document.status, document.progress_percent, document.progress_step, "Document re-queued for processing")
    return document


def export_document(document: DocumentJob, export_format: str) -> tuple[str, str]:
    payload = document.finalized_data or document.reviewed_data or document.extracted_data or {}
    if export_format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["field", "value"])
        for key, value in payload.items():
            writer.writerow([key, value])
        return "text/csv", output.getvalue()
    return "application/json", json.dumps(payload, indent=2, default=str)
