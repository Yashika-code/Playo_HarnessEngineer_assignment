from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


DocumentStatus = Literal["queued", "processing", "completed", "failed", "finalized"]


class DocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    file_type: str
    file_size: int
    status: DocumentStatus
    progress_step: str
    progress_percent: int
    created_at: datetime
    updated_at: datetime
    finalized_at: datetime | None = None


class DocumentDetail(DocumentSummary):
    storage_path: str
    extracted_data: dict[str, Any] | None = None
    reviewed_data: dict[str, Any] | None = None
    finalized_data: dict[str, Any] | None = None
    error_message: str | None = None
    completed_at: datetime | None = None


class ReviewPayload(BaseModel):
    reviewed_data: dict[str, Any] = Field(default_factory=dict)


class FinalizeResponse(BaseModel):
    status: str


class RetryResponse(BaseModel):
    status: str


class UploadResponse(BaseModel):
    created: list[DocumentSummary]


class ProgressEvent(BaseModel):
    document_id: UUID
    event: str
    status: str
    progress_percent: int
    progress_step: str
    message: str | None = None
    payload: dict[str, Any] | None = None


class ExportFormat(BaseModel):
    format: Literal["json", "csv"]
