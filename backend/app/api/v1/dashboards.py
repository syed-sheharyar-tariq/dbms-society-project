from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_role
from app.database import get_db
from app.models.entities import Profile
from app.schemas.report_schemas import DashboardSummaryResponse
from app.services.report_service import get_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
async def summary(
    profile: Profile = Depends(require_role("complaint_officer", "administrator")),
    db: AsyncSession = Depends(get_db),
):
    return await get_dashboard_summary(db)
