import io
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.core.errors import AppError
from app.core.files import upload


def test_disallowed_file_type_is_rejected() -> None:
    with pytest.raises(AppError) as error:
        upload(
            MagicMock(),
            stream=io.BytesIO(b"content"),
            filename="payload.exe",
            mime="application/x-msdownload",
            uploaded_by=uuid.uuid4(),
            owner_entity_type="test",
            owner_entity_id=uuid.uuid4(),
            scope_refs={},
        )
    assert error.value.code == "FILE_TYPE_REJECTED"


@patch("app.core.files.client")
def test_allowed_file_is_hashed(mock_client: MagicMock) -> None:
    db = MagicMock()
    row = upload(
        db,
        stream=io.BytesIO(b"pdf-content"),
        filename="document.pdf",
        mime="application/pdf",
        uploaded_by=uuid.uuid4(),
        owner_entity_type="test",
        owner_entity_id=uuid.uuid4(),
        scope_refs={},
    )
    assert row.sha256
    mock_client.return_value.put_object.assert_called_once()
