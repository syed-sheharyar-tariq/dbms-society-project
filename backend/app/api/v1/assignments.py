import math
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ForbiddenError
from app.core.permissions import get_current_profile, require_role
from app.database import get_db
from app.models.entities import (
    AssignmentUpdate,
    Incident,
    Profile,
    WorkAssignment,
)
from app.schemas.assignment_schemas import (
    AssignmentStatusUpdate,
    AssignmentUpdateResponse,
    WorkAssignmentCreate,
    WorkAssignmentResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.assignment_service import (
    create_work_assignment,
    update_assignment_status,
)

router = APIRouter(tags=["Work Assignments"])


def build_assignment_response(assignment: WorkAssignment) -> WorkAssignmentResponse:
    updates_resp = []
    if assignment.updates:
        for u in assignment.updates:
            updates_resp.append(
                AssignmentUpdateResponse(
                    id=u.id,
                    assignment_id=u.assignment_id,
                    actor_profile_id=u.actor_profile_id,
                    actor_name=u.actor.full_name if u.actor else None,
                    update_type=u.update_type,
                    message=u.message,
                    old_status=u.old_status,
                    new_status=u.new_status,
                    created_at=u.created_at,
                )
            )

    return WorkAssignmentResponse(
        id=assignment.id,
        incident_id=assignment.incident_id,
        incident_number=assignment.incident.incident_number if assignment.incident else None,
        incident_title=assignment.incident.title if assignment.incident else None,
        incident_priority=assignment.incident.priority if assignment.incident else None,
        area_description=assignment.incident.area_description if assignment.incident else None,
        category_name=assignment.incident.category.name if assignment.incident and assignment.incident.category else None,
        staff_profile_id=assignment.staff_profile_id,
        staff_name=assignment.staff_profile.full_name if assignment.staff_profile else None,
        assigned_by_profile_id=assignment.assigned_by_profile_id,
        status=assignment.status,
        assigned_at=assignment.assigned_at,
        accepted_at=assignment.accepted_at,
        started_at=assignment.started_at,
        completed_at=assignment.completed_at,
        completion_notes=assignment.completion_notes,
        ended_at=assignment.ended_at,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
        updates=updates_resp,
    )


@router.post("/incidents/{incident_id}/assignments", response_model=WorkAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_staff(
    incident_id: uuid.UUID,
    data: WorkAssignmentCreate,
    request: Request,
    profile: Profile = Depends(require_role("complaint_officer", "administrator")),
    db: AsyncSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    assignment = await create_work_assignment(db, incident_id, data, profile, request_id)
    
    # Reload with incident context
    stmt = (
        select(WorkAssignment)
        .options(
            selectinload(WorkAssignment.incident).selectinload(Incident.category),
            selectinload(WorkAssignment.staff_profile),
            selectinload(WorkAssignment.updates).selectinload(AssignmentUpdate.actor),
        )
        .where(WorkAssignment.id == assignment.id)
    )
    res = await db.execute(stmt)
    return build_assignment_response(res.scalars().first())


@router.get("/assignments", response_model=PaginatedResponse[WorkAssignmentResponse])
async def list_assignments(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(WorkAssignment)
        .options(
            selectinload(WorkAssignment.incident).selectinload(Incident.category),
            selectinload(WorkAssignment.staff_profile),
            selectinload(WorkAssignment.updates).selectinload(AssignmentUpdate.actor),
        )
    )

    # Scoping: field_staff can ONLY view their own assignments (AT-10)
    if profile.role == "field_staff":
        stmt = stmt.where(WorkAssignment.staff_profile_id == profile.id)
    elif profile.role not in ("complaint_officer", "administrator"):
        raise ForbiddenError("Access denied to work assignments.")

    if status_filter:
        stmt = stmt.where(WorkAssignment.status == status_filter)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar_one()

    stmt = stmt.order_by(desc(WorkAssignment.assigned_at)).offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(stmt)
    assignments = res.scalars().all()

    items = [build_assignment_response(a) for a in assignments]
    pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.patch("/assignments/{assignment_id}", response_model=WorkAssignmentResponse)
async def update_assignment(
    assignment_id: uuid.UUID,
    data: AssignmentStatusUpdate,
    request: Request,
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    assignment = await update_assignment_status(db, assignment_id, data, profile, request_id)
    
    stmt = (
        select(WorkAssignment)
        .options(
            selectinload(WorkAssignment.incident).selectinload(Incident.category),
            selectinload(WorkAssignment.staff_profile),
            selectinload(WorkAssignment.updates).selectinload(AssignmentUpdate.actor),
        )
        .where(WorkAssignment.id == assignment.id)
    )
    res = await db.execute(stmt)
    return build_assignment_response(res.scalars().first())
