import datetime
import uuid
from typing import Optional
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import BadRequestError, ConflictError, NotFoundError
from app.models.entities import (
    Category,
    Complaint,
    ComplaintStatusHistory,
    Incident,
    IncidentComplaintLink,
    IncidentStatusHistory,
    Profile,
)
from app.schemas.incident_schemas import IncidentCreate, IncidentLinkCreate
from app.services.audit_service import log_audit_event


async def generate_incident_number(db: AsyncSession) -> str:
    year = datetime.datetime.now(datetime.timezone.utc).year
    try:
        seq_res = await db.execute(text("SELECT nextval('incident_number_seq')"))
        seq_val = seq_res.scalar_one()
    except Exception:
        count_res = await db.execute(select(func.count(Incident.id)))
        seq_val = (count_res.scalar() or 0) + 1
    return f"INC-{year}-{seq_val:06d}"


async def create_incident(
    db: AsyncSession,
    data: IncidentCreate,
    creator_profile: Profile,
    request_id: Optional[str] = None,
) -> Incident:
    cat = await db.get(Category, data.category_id)
    if not cat or not cat.is_active:
        raise BadRequestError("Invalid or inactive incident category.")

    inc_no = await generate_incident_number(db)
    now = datetime.datetime.now(datetime.timezone.utc)

    incident = Incident(
        incident_number=inc_no,
        category_id=data.category_id,
        title=data.title,
        description=data.description,
        status="open",
        routing_type="unassigned",
        priority=data.priority,
        area_description=data.area_description,
        created_by=creator_profile.id,
        created_at=now,
    )
    db.add(incident)
    await db.flush()

    # Initial incident status history
    inc_hist = IncidentStatusHistory(
        incident_id=incident.id,
        old_status=None,
        new_status="open",
        changed_by_profile_id=creator_profile.id,
        reason="Initial incident creation",
    )
    db.add(inc_hist)

    # Link initial complaints atomically (AT-05)
    for c_id in data.complaint_ids:
        complaint = await db.get(Complaint, c_id)
        if not complaint:
            raise NotFoundError(f"Complaint {c_id} not found.")

        # Check existing active link
        active_link_check = await db.execute(
            select(IncidentComplaintLink).where(
                IncidentComplaintLink.complaint_id == c_id,
                IncidentComplaintLink.unlinked_at.is_(None),
            )
        )
        if active_link_check.scalars().first():
            raise ConflictError(f"Complaint {complaint.complaint_number} already has an active incident link.")

        link = IncidentComplaintLink(
            incident_id=incident.id,
            complaint_id=c_id,
            linked_by=creator_profile.id,
            linked_at=now,
        )
        db.add(link)

        # Update complaint status to under_review or in_progress
        if complaint.status == "submitted":
            complaint.status = "under_review"
            c_hist = ComplaintStatusHistory(
                complaint_id=complaint.id,
                old_status="submitted",
                new_status="under_review",
                changed_by_profile_id=creator_profile.id,
                reason=f"Grouped into incident {incident.incident_number}",
            )
            db.add(c_hist)

    await log_audit_event(
        db,
        action="CREATE_INCIDENT",
        entity_type="incidents",
        entity_id=incident.id,
        actor_profile_id=creator_profile.id,
        request_id=request_id,
        new_values={
            "incident_number": inc_no,
            "title": data.title,
            "linked_complaints": [str(cid) for cid in data.complaint_ids],
        },
    )

    await db.commit()
    await db.refresh(incident)
    return incident


async def link_complaint_to_incident(
    db: AsyncSession,
    incident_id: uuid.UUID,
    data: IncidentLinkCreate,
    officer_profile: Profile,
    request_id: Optional[str] = None,
) -> IncidentComplaintLink:
    incident = await db.get(Incident, incident_id)
    if not incident:
        raise NotFoundError("Incident not found.")

    complaint = await db.get(Complaint, data.complaint_id)
    if not complaint:
        raise NotFoundError("Complaint not found.")

    # Check category compatibility
    if complaint.category_id != incident.category_id and not data.override_category_mismatch:
        raise BadRequestError(
            "Complaint category does not match incident category. Set override_category_mismatch=true with reason to proceed."
        )

    # Check if complaint already has an active link (AT-06)
    existing_link_res = await db.execute(
        select(IncidentComplaintLink).where(
            IncidentComplaintLink.complaint_id == complaint.id,
            IncidentComplaintLink.unlinked_at.is_(None),
        )
    )
    if existing_link_res.scalars().first():
        raise ConflictError("Complaint already has an active incident link.")

    now = datetime.datetime.now(datetime.timezone.utc)
    link = IncidentComplaintLink(
        incident_id=incident.id,
        complaint_id=complaint.id,
        linked_by=officer_profile.id,
        linked_at=now,
    )
    db.add(link)

    # Advance complaint status
    old_c_status = complaint.status
    if incident.status in ("in_progress", "assigned") and complaint.status in ("submitted", "under_review"):
        complaint.status = "in_progress"
        db.add(
            ComplaintStatusHistory(
                complaint_id=complaint.id,
                old_status=old_c_status,
                new_status="in_progress",
                changed_by_profile_id=officer_profile.id,
                reason=f"Linked to active incident {incident.incident_number}",
            )
        )

    await log_audit_event(
        db,
        action="LINK_COMPLAINT_TO_INCIDENT",
        entity_type="incident_complaint_links",
        entity_id=link.id,
        actor_profile_id=officer_profile.id,
        request_id=request_id,
        new_values={"incident_id": str(incident.id), "complaint_id": str(complaint.id)},
    )

    await db.commit()
    await db.refresh(link)
    return link


async def unlink_complaint_from_incident(
    db: AsyncSession,
    link_id: uuid.UUID,
    unlink_reason: str,
    officer_profile: Profile,
    request_id: Optional[str] = None,
) -> IncidentComplaintLink:
    """Unlinks a complaint while preserving audit history (AT-07)."""
    link = await db.get(IncidentComplaintLink, link_id)
    if not link:
        raise NotFoundError("Incident-complaint link not found.")
    if link.unlinked_at is not None:
        raise ConflictError("Link has already been unlinked.")

    now = datetime.datetime.now(datetime.timezone.utc)
    link.unlinked_at = now
    link.unlinked_by = officer_profile.id
    link.unlink_reason = unlink_reason

    # Revert complaint to under_review
    complaint = await db.get(Complaint, link.complaint_id)
    if complaint and complaint.status == "in_progress":
        old_status = complaint.status
        complaint.status = "under_review"
        db.add(
            ComplaintStatusHistory(
                complaint_id=complaint.id,
                old_status=old_status,
                new_status="under_review",
                changed_by_profile_id=officer_profile.id,
                reason=f"Unlinked from incident with reason: {unlink_reason}",
            )
        )

    await log_audit_event(
        db,
        action="UNLINK_COMPLAINT_FROM_INCIDENT",
        entity_type="incident_complaint_links",
        entity_id=link.id,
        actor_profile_id=officer_profile.id,
        request_id=request_id,
        old_values={"unlinked_at": None},
        new_values={"unlinked_at": now.isoformat(), "unlink_reason": unlink_reason},
    )

    await db.commit()
    await db.refresh(link)
    return link


async def update_incident_status(
    db: AsyncSession,
    incident_id: uuid.UUID,
    new_status: str,
    reason: Optional[str],
    officer_profile: Profile,
    request_id: Optional[str] = None,
) -> Incident:
    stmt = (
        select(Incident)
        .where(Incident.id == incident_id)
        .options(
            selectinload(Incident.complaint_links).selectinload(IncidentComplaintLink.complaint),
        )
        .with_for_update()
    )
    res = await db.execute(stmt)
    incident = res.scalars().first()
    if not incident:
        raise NotFoundError("Incident not found.")

    old_status = incident.status
    now = datetime.datetime.now(datetime.timezone.utc)

    # CRITICAL SYNCHRONIZATION (Section 5.6, AT-14):
    # When incident is marked 'resolved', each eligible active linked complaint moves to 'pending_confirmation', NOT 'closed'!
    if new_status == "resolved":
        incident.status = "resolved"
        incident.resolved_at = now

        for link in incident.complaint_links:
            if link.unlinked_at is None:
                complaint = link.complaint
                # Eligible statuses: under_review, in_progress, reopened
                if complaint.status in ("under_review", "in_progress", "reopened"):
                    old_c_status = complaint.status
                    complaint.status = "pending_confirmation"
                    complaint.resolved_reported_at = now

                    db.add(
                        ComplaintStatusHistory(
                            complaint_id=complaint.id,
                            old_status=old_c_status,
                            new_status="pending_confirmation",
                            changed_by_profile_id=officer_profile.id,
                            reason=f"Incident {incident.incident_number} resolved by field team/officer",
                        )
                    )
    elif new_status == "closed":
        # Incident close check: ensure no active complaints are still pending confirmation
        incident.status = "closed"
        incident.closed_at = now
    else:
        incident.status = new_status

    # Record incident status history
    db.add(
        IncidentStatusHistory(
            incident_id=incident.id,
            old_status=old_status,
            new_status=new_status,
            changed_by_profile_id=officer_profile.id,
            reason=reason or f"Status updated to {new_status}",
        )
    )

    await log_audit_event(
        db,
        action="UPDATE_INCIDENT_STATUS",
        entity_type="incidents",
        entity_id=incident.id,
        actor_profile_id=officer_profile.id,
        request_id=request_id,
        old_values={"status": old_status},
        new_values={"status": new_status, "reason": reason},
    )

    await db.commit()
    await db.refresh(incident)
    return incident
