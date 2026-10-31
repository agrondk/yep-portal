from app.core.audit import AuditInput, _redact


def test_sensitive_audit_fields_are_redacted() -> None:
    values = _redact({"email": "person@example.test", "password": "secret", "token": "raw"})
    assert values["email"] == "person@example.test"
    assert values["password"] == "[REDACTED]"
    assert values["token"] == "[REDACTED]"


def test_audit_input_defaults_to_success() -> None:
    assert AuditInput(action="test.action").outcome == "succeeded"
