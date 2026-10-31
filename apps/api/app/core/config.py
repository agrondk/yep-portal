from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../../.env", ".env"), extra="ignore")

    app_env: str = "development"
    app_name: str = "YEP Portal API"
    api_v1_prefix: str = "/api/v1"
    web_origins: list[str] = ["http://127.0.0.1:3000", "http://localhost:3000"]
    database_url: str = Field(
        default="postgresql+psycopg://yep:yep_dev_password@localhost:5432/yep"
    )
    celery_broker_url: str = "redis://localhost:6379/0"
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "yep_minio"
    s3_secret_key: str = "change-me"
    s3_private_bucket: str = "yep-private"
    s3_region: str = "us-east-1"
    file_max_bytes: int = 10_485_760
    file_url_ttl_seconds: int = 300
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_from: str = "yep_info@youngengineers.org"
    session_cookie_secure: bool = False
    session_ttl_hours: int = 12
    token_ttl_minutes: int = 30
    invitation_ttl_days: int = 7
    mfa_required_for_privileged: bool = True
    mfa_encryption_key: str = ""
    organization_timezone: str = "Europe/Belgrade"
    default_locale: str = "sq"


@lru_cache
def get_settings() -> Settings:
    return Settings()
