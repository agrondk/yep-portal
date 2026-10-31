import hashlib
import uuid
from datetime import UTC, datetime
from typing import BinaryIO

import boto3
from botocore.client import BaseClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.modules.core.models import FileObject

ALLOWED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png"}


def client() -> BaseClient:
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
    )


def upload(
    db: Session,
    *,
    stream: BinaryIO,
    filename: str,
    mime: str,
    uploaded_by: uuid.UUID,
    owner_entity_type: str,
    owner_entity_id: uuid.UUID,
    scope_refs: dict[str, str],
) -> FileObject:
    settings = get_settings()
    if mime not in ALLOWED_MIME_TYPES:
        raise AppError("FILE_TYPE_REJECTED", "This file type is not allowed.", 415)
    content = stream.read(settings.file_max_bytes + 1)
    if len(content) > settings.file_max_bytes:
        raise AppError("FILE_TOO_LARGE", "The file exceeds the size limit.", 413)
    object_key = f"{owner_entity_type}/{owner_entity_id}/{uuid.uuid4()}"
    client().put_object(
        Bucket=settings.s3_private_bucket,
        Key=object_key,
        Body=content,
        ContentType=mime,
    )
    row = FileObject(
        bucket=settings.s3_private_bucket,
        object_key=object_key,
        original_name=filename,
        mime=mime,
        size=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
        owner_entity_type=owner_entity_type,
        owner_entity_id=owner_entity_id,
        uploaded_by=uploaded_by,
        scope_refs=scope_refs,
        created_at=datetime.now(UTC),
    )
    db.add(row)
    return row


def presigned_url(row: FileObject) -> str:
    settings = get_settings()
    return str(
        client().generate_presigned_url(
            "get_object",
            Params={"Bucket": row.bucket, "Key": row.object_key},
            ExpiresIn=settings.file_url_ttl_seconds,
        )
    )
