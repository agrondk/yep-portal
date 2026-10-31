import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class FileResponse(BaseModel):
    id: uuid.UUID
    original_name: str
    mime: str
    size: int
    sha256: str
    created_at: datetime


class FileUrlResponse(BaseModel):
    url: str
    expires_in: int


class AuditResponse(BaseModel):
    id: uuid.UUID
    occurred_at: datetime
    action: str
    outcome: str
    actor_id: uuid.UUID | None
    entity_type: str | None
    entity_id: uuid.UUID | None
    reason: str | None


class JobResponse(BaseModel):
    id: uuid.UUID
    job_name: str
    started_at: datetime
    finished_at: datetime | None
    outcome: str | None
    detail: dict[str, Any]
