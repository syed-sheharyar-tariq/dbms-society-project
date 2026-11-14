from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_role
from app.database import get_db
from app.models.entities import Profile
from app.schemas.report_schemas import (
    RecurringFaultItem,
    StaffWorkloadItem,
    UtilityPerformanceItem,
)
from app.services.report_service import (
    get_recurring_fault_report,
    get_staff_workload_report,
    get_utility_performance_report,
)

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])


@router.get("/recurring-faults", response_model=List[RecurringFaultItem])
async def recurring_faults(
    days: int = Query(90, ge=7, le=365),
    profile: Profile = Depends(require_role("complaint_officer", "administrator")),
    db: AsyncSession = Depends(get_db),
):
    return await get_recurring_fault_report(db, days)


@router.get("/staff-workload", response_model=List[StaffWorkloadItem])
async def staff_workload(
    profile: Profile = Depends(require_role("complaint_officer", "administrator")),
    db: AsyncSession = Depends(get_db),
):
    return await get_staff_workload_report(db)


@router.get("/utility-response-times", response_model=List[UtilityPerformanceItem])
async def utility_response_times(
    profile: Profile = Depends(require_role("complaint_officer", "administrator")),
    db: AsyncSession = Depends(get_db),
):
    return await get_utility_performance_report(db)
