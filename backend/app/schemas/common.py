from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    code: str
    message: str
    request_id: Optional[str] = None
    field_errors: Optional[List[dict]] = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)
    pages: int


class HealthStatus(BaseModel):
    status: str
    app: str
    version: str
