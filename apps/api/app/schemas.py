from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: str | None = None


class ApiError(BaseModel):
    code: str
    message: str
    details: dict[str, object] = {}
