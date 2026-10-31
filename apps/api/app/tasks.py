import smtplib
from datetime import UTC, datetime
from email.message import EmailMessage

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.modules.core.models import JobRun, OutboxMessage
from app.worker import celery_app


@celery_app.task(  # type: ignore[misc]
    name="app.tasks.deliver_outbox", autoretry_for=(OSError,), retry_backoff=True, max_retries=3
)
def deliver_outbox() -> int:
    started = datetime.now(UTC)
    delivered = 0
    with SessionLocal.begin() as db:
        run = JobRun(job_name="deliver_outbox", started_at=started, detail={})
        db.add(run)
        messages = list(
            db.scalars(
                select(OutboxMessage)
                .where(OutboxMessage.status == "queued")
                .with_for_update(skip_locked=True)
                .limit(100)
            )
        )
        settings = get_settings()
        for row in messages:
            row.attempts += 1
            try:
                if settings.app_env == "development":
                    row.status = "dev_captured"
                elif row.channel == "email" and row.recipient_email:
                    message = EmailMessage()
                    message["From"] = settings.smtp_from
                    message["To"] = row.recipient_email
                    message["Subject"] = row.template_key
                    message.set_content(str(row.payload))
                    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
                        smtp.send_message(message)
                    row.status = "sent"
                else:
                    row.status = "failed"
                    row.last_error = "Unsupported channel or missing recipient"
                row.sent_at = datetime.now(UTC)
                delivered += 1
            except Exception as exc:
                row.last_error = str(exc)[:1000]
                row.status = "failed" if row.attempts >= 3 else "queued"
                raise
        run.finished_at = datetime.now(UTC)
        run.outcome = "succeeded"
        run.detail = {"delivered": delivered}
    return delivered
