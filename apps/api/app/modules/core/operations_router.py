import json
import uuid

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import audit
from app.core.authorization import PermissionContext, require_permission
from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import AppError
from app.core.files import presigned_url, upload
from app.modules.core.models import AuditEvent, FileObject, JobRun, Role, ScopeType
from app.modules.core.operations_schemas import (
    AuditResponse,
    FileResponse,
    FileUrlResponse,
    JobResponse,
)

router = APIRouter(tags=["operations"])


def _can_access_file(permission: PermissionContext, row: FileObject) -> bool:
    for assignment in permission.assignments:
        if (
            assignment.role is Role.OWNER_ADMIN
            and assignment.scope_type is ScopeType.ORGANIZATION
            and assignment.scope_id is None
        ):
            return True
        value = row.scope_refs.get(assignment.scope_type.value)
        if assignment.scope_id is not None and value == str(assignment.scope_id):
            return True
    return False


@router.post("/files", response_model=FileResponse, status_code=201)
def upload_file(
    request: Request,
    file: UploadFile = File(...),
    owner_entity_type: str = Form(...),
    owner_entity_id: uuid.UUID = Form(...),
    scope_refs_json: str = Form("{}"),
    permission: PermissionContext = Depends(require_permission("core.file.create")),
    db: Session = Depends(get_db),
) -> FileResponse:
    try:
        scope_refs = json.loads(scope_refs_json)
    except json.JSONDecodeError as exc:
        raise AppError("SCOPE_REFS_INVALID", "Scope references must be valid JSON.", 400) from exc
    row = upload(
        db,
        stream=file.file,
        filename=file.filename or "upload",
        mime=file.content_type or "application/octet-stream",
        uploaded_by=permission.auth.user.id,
        owner_entity_type=owner_entity_type,
        owner_entity_id=owner_entity_id,
        scope_refs=scope_refs,
    )
    audit.record(
        db,
        audit.AuditInput(
            action="file.uploaded",
            actor_id=permission.auth.user.id,
            entity_type="file_object",
            entity_id=row.id,
            correlation_id=uuid.UUID(request.state.request_id),
        ),
    )
    db.commit()
    db.refresh(row)
    return FileResponse.model_validate(row, from_attributes=True)


@router.get("/files/{file_id}/url", response_model=FileUrlResponse)
def file_url(
    file_id: uuid.UUID,
    request: Request,
    permission: PermissionContext = Depends(require_permission("core.file.view")),
    db: Session = Depends(get_db),
) -> FileUrlResponse:
    row = db.get(FileObject, file_id)
    if row is None or row.deleted_at is not None:
        raise AppError("FILE_NOT_FOUND", "File not found.", 404)
    if not _can_access_file(permission, row):
        audit.record_failure(
            audit.AuditInput(
                action="file.downloaded",
                actor_id=permission.auth.user.id,
                outcome="denied",
                reason="scope_denied",
                entity_type="file_object",
                entity_id=row.id,
                correlation_id=uuid.UUID(request.state.request_id),
            )
        )
        raise AppError("SCOPE_DENIED", "This file is outside your assigned scope.", 403)
    audit.record(
        db,
        audit.AuditInput(
            action="file.downloaded",
            actor_id=permission.auth.user.id,
            entity_type="file_object",
            entity_id=row.id,
            correlation_id=uuid.UUID(request.state.request_id),
        ),
    )
    db.commit()
    return FileUrlResponse(url=presigned_url(row), expires_in=get_settings().file_url_ttl_seconds)


@router.get("/admin/audit-events", response_model=list[AuditResponse])
def audit_events(
    page: int = 1,
    page_size: int = 50,
    _permission: PermissionContext = Depends(require_permission("core.audit.view")),
    db: Session = Depends(get_db),
) -> list[AuditResponse]:
    size = min(max(page_size, 1), 100)
    rows = db.scalars(
        select(AuditEvent)
        .order_by(AuditEvent.occurred_at.desc())
        .offset((max(page, 1) - 1) * size)
        .limit(size)
    )
    return [AuditResponse.model_validate(row, from_attributes=True) for row in rows]


@router.get("/admin/jobs", response_model=list[JobResponse])
def jobs(
    _permission: PermissionContext = Depends(require_permission("core.job.view")),
    db: Session = Depends(get_db),
) -> list[JobResponse]:
    rows = db.scalars(select(JobRun).order_by(JobRun.started_at.desc()).limit(100))
    return [JobResponse.model_validate(row, from_attributes=True) for row in rows]
