import datetime
from typing import List
from sqlalchemy import case, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import (
    Block,
    Category,
    Complaint,
    Incident,
    IncidentComplaintLink,
    Profile,
    Property,
    UtilityCase,
    UtilityCompany,
    WorkAssignment,
)
from app.schemas.report_schemas import (
    DashboardSummaryResponse,
    RecurringFaultItem,
    StaffWorkloadItem,
    UtilityPerformanceItem,
)


async def get_dashboard_summary(db: AsyncSession) -> DashboardSummaryResponse:
    now = datetime.datetime.now(datetime.timezone.utc)

    # 1. New complaints (submitted)
    new_c_res = await db.execute(
        select(func.count(Complaint.id)).where(Complaint.status == "submitted")
    )
    new_c = new_c_res.scalar_one()

    # 2. Pending complaints (not closed, not cancelled)
    pending_c_res = await db.execute(
        select(func.count(Complaint.id)).where(Complaint.status.not_in(["closed", "cancelled"]))
    )
    pending_c = pending_c_res.scalar_one()

    # 3. Open incidents
    open_inc_res = await db.execute(
        select(func.count(Incident.id)).where(Incident.status.not_in(["closed", "cancelled"]))
    )
    open_inc = open_inc_res.scalar_one()

    # 4. Pending confirmations
    conf_res = await db.execute(
        select(func.count(Complaint.id)).where(Complaint.status == "pending_confirmation")
    )
    conf_c = conf_res.scalar_one()

    # 5. Overdue utility cases (due date exists, in past, not terminal)
    overdue_res = await db.execute(
        select(func.count(UtilityCase.id)).where(
            UtilityCase.expected_resolution_at.is_not(None),
            UtilityCase.expected_resolution_at < now,
            UtilityCase.status.not_in(["resolved", "closed", "cancelled"]),
        )
    )
    overdue_u = overdue_res.scalar_one()

    # 6. Urgent open items
    urgent_c_res = await db.execute(
        select(func.count(Complaint.id)).where(
            Complaint.is_urgent.is_(True),
            Complaint.status.not_in(["closed", "cancelled"]),
        )
    )
    urgent_c = urgent_c_res.scalar_one()

    return DashboardSummaryResponse(
        new_complaints_count=new_c,
        pending_complaints_count=pending_c,
        open_incidents_count=open_inc,
        pending_confirmations_count=conf_c,
        overdue_utility_cases_count=overdue_u,
        urgent_open_items_count=urgent_c,
    )


async def get_recurring_fault_report(db: AsyncSession, days: int = 90) -> List[RecurringFaultItem]:
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)

    stmt = (
        select(
            func.coalesce(Block.name, "General Society").label("block_name"),
            Category.name.label("category_name"),
            Incident.area_description,
            func.count(distinct(Incident.id)).label("incident_count"),
        )
        .join(Category, Incident.category_id == Category.id)
        .outerjoin(IncidentComplaintLink, Incident.id == IncidentComplaintLink.incident_id)
        .outerjoin(Complaint, IncidentComplaintLink.complaint_id == Complaint.id)
        .outerjoin(Property, Complaint.property_id == Property.id)
        .outerjoin(Block, Property.block_id == Block.id)
        .where(Incident.created_at >= cutoff)
        .group_by(Block.name, Category.name, Incident.area_description)
        .order_by(func.count(distinct(Incident.id)).desc())
    )

    res = await db.execute(stmt)
    items = []
    for row in res.all():
        items.append(
            RecurringFaultItem(
                block_name=row.block_name,
                category_name=row.category_name,
                area_description=row.area_description,
                incident_count=row.incident_count,
            )
        )
    return items


async def get_staff_workload_report(db: AsyncSession) -> List[StaffWorkloadItem]:
    stmt = (
        select(
            Profile.id.label("staff_profile_id"),
            Profile.full_name.label("staff_name"),
            func.count(case((WorkAssignment.status == "assigned", 1))).label("assigned_count"),
            func.count(case((WorkAssignment.status == "in_progress", 1))).label("in_progress_count"),
            func.count(case((WorkAssignment.status == "blocked", 1))).label("blocked_count"),
            func.count(WorkAssignment.id).label("total_active"),
        )
        .join(WorkAssignment, Profile.id == WorkAssignment.staff_profile_id)
        .where(
            Profile.role == "field_staff",
            Profile.is_active.is_(True),
            WorkAssignment.status.in_(["assigned", "accepted", "in_progress", "blocked"]),
            WorkAssignment.ended_at.is_(None),
        )
        .group_by(Profile.id, Profile.full_name)
    )

    res = await db.execute(stmt)
    items = []
    for row in res.all():
        items.append(
            StaffWorkloadItem(
                staff_profile_id=row.staff_profile_id,
                staff_name=row.staff_name,
                assigned_count=row.assigned_count,
                in_progress_count=row.in_progress_count,
                blocked_count=row.blocked_count,
                total_active=row.total_active,
            )
        )
    return items


async def get_utility_performance_report(db: AsyncSession) -> List[UtilityPerformanceItem]:
    stmt = (
        select(
            UtilityCompany.id.label("utility_company_id"),
            UtilityCompany.name.label("utility_name"),
            func.count(UtilityCase.id).label("total_cases"),
            func.count(UtilityCase.first_response_at).label("sample_count"),
        )
        .outerjoin(UtilityCase, UtilityCompany.id == UtilityCase.utility_company_id)
        .group_by(UtilityCompany.id, UtilityCompany.name)
    )

    res = await db.execute(stmt)
    items = []
    for row in res.all():
        items.append(
            UtilityPerformanceItem(
                utility_company_id=row.utility_company_id,
                utility_name=row.utility_name,
                total_cases=row.total_cases,
                sample_count=row.sample_count,
            )
        )
    return items
