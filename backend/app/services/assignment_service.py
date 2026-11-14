import datetime
import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import BadRequestError, ForbiddenError, NotFoundError
from app.models.entities import (
    AssignmentUpdate,
    Incident,
    Profile,
    WorkAssignment,
)
from app.schemas.assignment_schemas import AssignmentStatusUpdate, WorkAssignmentCreate
from app.services.audit_service import log_audit_event


async def create_work_assignment(
    db: AsyncSession,
    incident_id: uuid.UUID,
    data: WorkAssignmentCreate,
    officer_profile: Profile,
    request_id: Optional[str] = None,
) -> WorkAssignment:
    incident = await db.get(Incident, incident_id)
    if not incident:
        raise NotFoundError("Incident not found.")

    # Verify staff profile role is field_staff (AT-08)
    staff = await db.get(Profile, data.staff_profile_id)
    if not staff:
        raise NotFoundError("Staff member not found.")
    if staff.role != "field_staff" or not staff.is_active:
        raise BadRequestError("Work assignments can only be allocated to active field_staff.")

    now = datetime.datetime.now(datetime.timezone.utc)

    # Check for existing active assignment on this incident; end it if reassigning (AT-09)
    stmt = select(WorkAssignment).where(
        WorkAssignment.incident_id == incident_id,
        WorkAssignment.status.in_(["assigned", "accepted", "in_progress", "blocked"]),
        WorkAssignment.ended_at.is_(None),
    )
    res = await db.execute(stmt)
    existing_assignment = res.scalars().first()
    if existing_assignment:
        existing_assignment.ended_at = now
        existing_assignment.status = "cancelled"
        db.add(
            AssignmentUpdate(
                assignment_id=existing_assignment.id,
                actor_profile_id=officer_profile.id,
                update_type="reassigned_away",
                message=f"Reassigned to staff {staff.full_name}",
                old_status=existing_assignment.status,
                new_status="cancelled",
                created_at=now,
            )
        )

    # Create new assignment
    assignment = WorkAssignment(
        incident_id=incident.id,
        staff_profile_id=staff.id,
        assigned_by_profile_id=officer_profile.id,
        status="assigned",
        assigned_at=now,
    )
    db.add(assignment)
    await db.flush()

    # Initial update
    db.add(
        AssignmentUpdate(
            assignment_id=assignment.id,
            actor_profile_id=officer_profile.id,
            update_type="assignment_created",
            message=data.notes or "Initial assignment created by officer",
            old_status=None,
            new_status="assigned",
            created_at=now,
        )
    )

    # Update incident routing and status
    incident.routing_type = "internal"
    if incident.status in ("open", "triaged"):
        incident.status = "assigned"

    await log_audit_event(
        db,
        action="ASSIGN_STAFF",
        entity_type="work_assignments",
        entity_id=assignment.id,
        actor_profile_id=officer_profile.id,
        request_id=request_id,
        new_values={
            "incident_id": str(incident.id),
            "staff_profile_id": str(staff.id),
            "assigned_by": str(officer_profile.id),
        },
    )

    await db.commit()
    await db.refresh(assignment)
    return assignment


async def update_assignment_status(
    db: AsyncSession,
    assignment_id: uuid.UUID,
    data: AssignmentStatusUpdate,
    actor_profile: Profile,
    request_id: Optional[str] = None,
) -> WorkAssignment:
    stmt = (
        select(WorkAssignment)
        .where(WorkAssignment.id == assignment_id)
        .options(selectinload(WorkAssignment.incident))
        .with_for_update()
    )
    res = await db.execute(stmt)
    assignment = res.scalars().first()
    if not assignment:
        raise NotFoundError("Work assignment not found.")

    # Authorization: Staff can only update their own assignment (AT-10)
    if actor_profile.role == "field_staff" and assignment.staff_profile_id != actor_profile.id:
        raise ForbiddenError("You cannot modify assignments allocated to other staff.")

    old_status = assignment.status
    now = datetime.datetime.now(datetime.timezone.utc)

    if data.status == "accepted" and not assignment.accepted_at:
        assignment.accepted_at = now
    elif data.status == "in_progress" and not assignment.started_at:
        assignment.started_at = now
        if assignment.incident.status in ("open", "triaged", "assigned"):
            assignment.incident.status = "in_progress"
    elif data.status == "completed":
        if not data.completion_notes:
            raise BadRequestError("Completion notes are mandatory when marking work completed.")
        assignment.completed_at = now
        assignment.completion_notes = data.completion_notes
        # Note: Completing assignment does NOT automatically resolve incident! (Section 4.3)
    elif data.status == "cancelled":
        assignment.ended_at = now

    assignment.status = data.status

    # Add append-only update
    db.add(
        AssignmentUpdate(
            assignment_id=assignment.id,
            actor_profile_id=actor_profile.id,
            update_type="status_change",
            message=data.notes or f"Status updated to {data.status}",
            old_status=old_status,
            new_status=data.status,
            created_at=now,
        )
    )

    await log_audit_event(
        db,
        action="UPDATE_ASSIGNMENT_STATUS",
        entity_type="work_assignments",
        entity_id=assignment.id,
        actor_profile_id=actor_profile.id,
        request_id=request_id,
        old_values={"status": old_status},
        new_values={"status": data.status},
    )

    await db.commit()
    await db.refresh(assignment)
    return assignment
