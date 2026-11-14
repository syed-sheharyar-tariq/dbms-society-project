from fastapi import APIRouter
from app.api.v1.admin import router as admin_router
from app.api.v1.assignments import router as assignments_router
from app.api.v1.attachments import router as attachments_router
from app.api.v1.auth import router as auth_router
from app.api.v1.complaints import router as complaints_router
from app.api.v1.dashboards import router as dashboards_router
from app.api.v1.incidents import router as incidents_router
from app.api.v1.reports import router as reports_router
from app.api.v1.society import router as society_router
from app.api.v1.utilities import router as utilities_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(society_router)
api_router.include_router(complaints_router)
api_router.include_router(incidents_router)
api_router.include_router(assignments_router)
api_router.include_router(utilities_router)
api_router.include_router(dashboards_router)
api_router.include_router(reports_router)
api_router.include_router(admin_router)
api_router.include_router(attachments_router)
