from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import register_error_handlers
from app.core.idempotency_middleware import IdempotencyMiddleware
from app.core.request_id import RequestIdMiddleware
from app.modules.catalog.router import public_router as catalog_public_router
from app.modules.catalog.router import router as catalog_router
from app.modules.core.access_router import router as access_router
from app.modules.core.auth_router import router as auth_router
from app.modules.core.operations_router import router as operations_router
from app.schemas import HealthResponse

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.web_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(IdempotencyMiddleware)
register_error_handlers(app)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(access_router, prefix=settings.api_v1_prefix)
app.include_router(operations_router, prefix=settings.api_v1_prefix)
app.include_router(catalog_router, prefix=settings.api_v1_prefix)
app.include_router(catalog_public_router, prefix=settings.api_v1_prefix)


@app.get("/health/live", response_model=HealthResponse, tags=["health"])
def live() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/health/ready", response_model=HealthResponse, tags=["health"])
def ready(db: Session = Depends(get_db)) -> HealthResponse:
    db.execute(text("SELECT 1"))
    return HealthResponse(status="ok", database="ok")
