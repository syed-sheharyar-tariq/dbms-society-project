import datetime
import uuid
from typing import Optional
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.core.permissions import check_property_authorization
from app.models.entities import (
    Category,
    Complaint,
    ComplaintStatusHistory,
    IncidentComplaintLink,
    Profile,
    Property,
    Resident,
    ResolutionConfirmation,
)
from app.schemas.complaint_schemas import (
    ComplaintCreate,
    OfflineComplaintCreate,
    ResolutionConfirmationCreate,
)
from app.services.audit_service import log_audit_event


async def generate_complaint_number(db: AsyncSession) -> str:
    """Generates human-readable unique complaint number format CMS-YYYY-000001."""
    year = datetime.datetime.now(datetime.timezone.utc).year
    try:
        seq_res = await db.execute(text("SELECT nextval('complaint_number_seq')"))
        seq_val = seq_res.scalar_one()
    except Exception:
        # Fallback if running outside PostgreSQL (e.g. SQLite tests)
        count_res = await db.execute(select(func.count(Complaint.id)))
        seq_val = (count_res.scalar() or 0) + 1
    return f"CMS-{year}-{seq_val:06d}"


async def create_resident_complaint(
    db: AsyncSession,
    data: ComplaintCreate,
    current_resident: Resident,
    current_profile: Profile,
    request_id: Optional[str] = None,
) -> Complaint:
    # 1. Verify that the resident has an authorized active association with the property (AT-02)
    is_auth = await check_property_authorization(db, current_resident.id, data.property_id)
    if not is_auth:
        raise ForbiddenError("Resident is not authorized to submit complaints for this property.")

    # 2. Verify category exists and is active
    cat = await db.get(Category, data.category_id)
    if not cat or not cat.is_active:
        raise BadRequestError("Selected category is invalid or inactive.")

    # 3. Generate sequential unique complaint number
    complaint_no = await generate_complaint_number(db)

    # 4. Insert Complaint, Status History and Audit in atomic transaction (AT-01)
    complaint = Complaint(
        complaint_number=complaint_no,
        resident_id=current_resident.id,
        property_id=data.property_id,
        category_id=data.category_id,
        description=data.description,
        status="submitted",
        is_urgent=data.is_urgent,
        urgency_reason=data.urgency_reason,
        intake_channel="portal",
        submitted_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.add(complaint)
    await db.flush()

    # Initial status history
    history = ComplaintStatusHistory(
        complaint_id=complaint.id,
        old_status=None,
        new_status="submitted",
        changed_by_profile_id=current_profile.id,
        reason="Initial resident portal submission",
    )
    db.add(history)

    # Audit log
    await log_audit_event(
        db,
        action="CREATE_COMPLAINT",
        entity_type="complaints",
        entity_id=complaint.id,
        actor_profile_id=current_profile.id,
        request_id=request_id,
        new_values={
            "complaint_number": complaint_no,
            "property_id": str(data.property_id),
            "category_id": str(data.category_id),
            "is_urgent": data.is_urgent,
        },
    )

    await db.commit()
    await db.refresh(complaint)
    return complaint


async def create_offline_complaint(
    db: AsyncSession,
    data: OfflineComplaintCreate,
    officer_profile: Profile,
    request_id: Optional[str] = None,
) -> Complaint:
    """Allows a Complaint Officer to record walk-in/phone/WhatsApp complaints (PR-12, AT-03)."""
    # 1. Verify resident exists
    resident = await db.get(Resident, data.resident_id)
    if not resident:
        raise NotFoundError("Referenced resident was not found.")

    # 2. Verify property association
    is_auth = await check_property_authorization(db, resident.id, data.property_id)
    if not is_auth:
        raise BadRequestError("The specified resident is not actively associated with this property.")

    # 3. Verify category
    cat = await db.get(Category, data.category_id)
    if not cat or not cat.is_active:
        raise BadRequestError("Selected category is invalid or inactive.")

    complaint_no = await generate_complaint_number(db)
    complaint = Complaint(
        complaint_number=complaint_no,
        resident_id=resident.id,
        property_id=data.property_id,
        category_id=data.category_id,
        description=data.description,
        status="submitted",
        is_urgent=data.is_urgent,
        urgency_reason=data.urgency_reason,
        intake_channel=data.intake_channel,
        recorded_by_profile_id=officer_profile.id,
        submitted_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.add(complaint)
    await db.flush()

    history = ComplaintStatusHistory(
        complaint_id=complaint.id,
        old_status=None,
        new_status="submitted",
        changed_by_profile_id=officer_profile.id,
        reason=f"Offline intake registered via {data.intake_channel} by officer {officer_profile.full_name}",
    )
    db.add(history)

    await log_audit_event(
        db,
        action="CREATE_OFFLINE_COMPLAINT",
        entity_type="complaints",
        entity_id=complaint.id,
        actor_profile_id=officer_profile.id,
        request_id=request_id,
        new_values={
            "complaint_number": complaint_no,
            "intake_channel": data.intake_channel,
            "resident_id": str(resident.id),
        },
    )

    await db.commit()
    await db.refresh(complaint)
    return complaint


async def get_complaint_detail(
    db: AsyncSession,
    complaint_id: uuid.UUID,
    current_profile: Profile,
    current_resident: Optional[Resident] = None,
) -> Complaint:
    stmt = (
        select(Complaint)
        .options(
            selectinload(Complaint.resident).selectinload(Resident.profile),
            selectinload(Complaint.property).selectinload(Property.block),
            selectinload(Complaint.category),
            selectinload(Complaint.status_history).selectinload(ComplaintStatusHistory.changed_by),
            selectinload(Complaint.confirmations),
            selectinload(Complaint.incident_links).selectinload(IncidentComplaintLink.incident),
        )
        .where(Complaint.id == complaint_id)
    )
    res = await db.execute(stmt)
    complaint = res.scalars().first()

    if not complaint:
        raise NotFoundError(f"Complaint {complaint_id} not found.")

    # Cross-resident authorization privacy check (AT-19)
    if current_profile.role == "resident":
        if not current_resident or complaint.resident_id != current_resident.id:
            raise ForbiddenError("You do not have permission to view another resident's complaint.")

    return complaint


async def submit_resident_confirmation(
    db: AsyncSession,
    complaint_id: uuid.UUID,
    data: ResolutionConfirmationCreate,
    current_resident: Resident,
    current_profile: Profile,
    request_id: Optional[str] = None,
) -> Complaint:
    """
    Handles independent resident confirmation or rejection (PR-10, AT-14 to AT-17).
    """
    stmt = select(Complaint).where(Complaint.id == complaint_id).with_for_update()
    res = await db.execute(stmt)
    complaint = res.scalars().first()

    if not complaint:
        raise NotFoundError("Complaint not found.")

    # Verify authorization: only the submitting resident can confirm
    if complaint.resident_id != current_resident.id:
        raise ForbiddenError("Only the submitting resident can confirm or reject resolution for this complaint.")

    # Must be in pending_confirmation
    if complaint.status != "pending_confirmation":
        raise ConflictError(f"Complaint is in state '{complaint.status}', not 'pending_confirmation'.")

    # Determine next cycle number
    cycle_res = await db.execute(
        select(func.coalesce(func.max(ResolutionConfirmation.cycle_number), 0))
        .where(ResolutionConfirmation.complaint_id == complaint.id)
    )
    next_cycle = cycle_res.scalar_one() + 1

    confirmation = ResolutionConfirmation(
        complaint_id=complaint.id,
        resident_id=current_resident.id,
        cycle_number=next_cycle,
        outcome=data.outcome,
        feedback=data.feedback,
        responded_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.add(confirmation)

    old_status = complaint.status
    if data.outcome == "confirmed":
        complaint.status = "closed"
        complaint.closed_at = datetime.datetime.now(datetime.timezone.utc)
        history_reason = "Resident confirmed satisfactory resolution."
    else:
        # Rejected (AT-16) -> reopens complaint
        complaint.status = "reopened"
        history_reason = f"Resident rejected resolution: {data.feedback or 'No feedback provided'}"

    history = ComplaintStatusHistory(
        complaint_id=complaint.id,
        old_status=old_status,
        new_status=complaint.status,
        changed_by_profile_id=current_profile.id,
        reason=history_reason,
    )
    db.add(history)

    await log_audit_event(
        db,
        action="RESIDENT_RESOLUTION_RESPONSE",
        entity_type="complaints",
        entity_id=complaint.id,
        actor_profile_id=current_profile.id,
        request_id=request_id,
        old_values={"status": old_status},
        new_values={"status": complaint.status, "outcome": data.outcome, "cycle": next_cycle},
    )

    await db.commit()
    await db.refresh(complaint)
    return complaint
