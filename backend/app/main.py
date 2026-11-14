import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import setup_logging
from app.database import check_db_ready
from app.schemas.common import HealthStatus
from app.api.v1.router import api_router

settings = get_settings()
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation
    yield
    # Shutdown cleanups


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Production-grade multi-role Complaint Management System for Gulistan-e-Jauhar, Karachi.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response


# Standardized Exception Handlers
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "request_id": request_id,
            "field_errors": exc.field_errors,
        },
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", None)
    formatted_errors = []
    for err in exc.errors():
        formatted_errors.append({
            "loc": err.get("loc"),
            "msg": err.get("msg"),
            "type": err.get("type"),
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": "VALIDATION_ERROR",
            "message": "Validation failed for request parameters or body.",
            "request_id": request_id,
            "field_errors": formatted_errors,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None)
    # Redact raw internal stack traces and SQL errors from client response
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected server error occurred. Please contact society administration.",
            "request_id": request_id,
        },
    )


# Health check endpoints
@app.get("/health/live", response_model=HealthStatus, tags=["Health"])
async def liveness():
    return HealthStatus(status="alive", app=settings.APP_NAME, version="1.0.0")


@app.get("/health/ready", response_model=HealthStatus, tags=["Health"])
async def readiness():
    is_ready = await check_db_ready()
    if not is_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "app": settings.APP_NAME, "version": "1.0.0"},
        )
    return HealthStatus(status="ready", app=settings.APP_NAME, version="1.0.0")


# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
