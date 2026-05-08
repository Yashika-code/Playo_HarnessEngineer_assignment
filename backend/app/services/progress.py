import json
from typing import Any
from uuid import UUID

import redis

from app.config import get_settings

settings = get_settings()


def publish_progress(document_id: UUID, event: str, status: str, progress_percent: int, progress_step: str, message: str | None = None, payload: dict[str, Any] | None = None) -> None:
    client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    message_body = {
        "document_id": str(document_id),
        "event": event,
        "status": status,
        "progress_percent": progress_percent,
        "progress_step": progress_step,
        "message": message,
        "payload": payload or {},
    }
    client.publish(f"document:{document_id}", json.dumps(message_body))
    client.close()
