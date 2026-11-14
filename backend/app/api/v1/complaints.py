import math
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ForbiddenError
from app.core.permissions import get_current_profile, get_current_resident, require_role
from app.database import get_db
from app.models.entities import (
    Complaint,
    ComplaintStatusHistory,
    IncidentComplaintLink,
    Profile,
    Property,
    Resident,
)
from app.schemas.common import PaginatedResponse
from app.schemas.complaint_schemas import (
    ComplaintCreate,
    ComplaintResponse,
    OfflineComplaintCreate,
    ResolutionConfirmationCreate,
    ResolutionConfirmationResponse,
)
from app.services.complaint_service import (
    create_offline_complaint,
    create_resident_complaint,
    get_complaint_detail,
    submit_resident_confirmation,
)

router = APIRouter(prefix="/complaints", tags=["Complaints"])


def build_complaint_response(complaint: Complaint) -> ComplaintResponse:
    active_inc_id = None
    active_inc_num = None
    if complaint.incident_links:
        for link in complaint.incident_links:
            if link.unlinked_at is None and link.incident:
                active_inc_id = link.incident.id
                active_inc_num = link.incident.incident_number
                break

    history_resp = []
    if complaint.status_history:
        for h in complaint.status_history:
            history_resp.append({
                "id": h.id,
                "old_status": h.old_status,
                "new_status": h.new_status,
                "reason": h.reason,
                "changed_at": h.changed_at,
                "changed_by_name": h.changed_by.full_name if h.changed_by else None,
            })

    conf_resp = []
    if complaint.confirmations:
        for c in complaint.confirmations:
            conf_resp.append(ResolutionConfirmationResponse.model_validate(c))

    return ComplaintResponse(
        id=complaint.id,
        complaint_number=complaint.complaint_number,
        resident_id=complaint.resident_id,
        resident_name=complaint.resident.profile.full_name if complaint.resident and complaint.resident.profile else None,
        property_id=complaint.property_id,
        property_number=complaint.property.property_number if complaint.property else None,
        block_name=complaint.property.block.name if complaint.property and complaint.property.block else None,
        category_id=complaint.category_id,
        category_name=complaint.category.name if complaint.category else None,
        description=complaint.description,
        status=complaint.status,
        is_urgent=complaint.is_urgent,
        urgency_reason=complaint.urgency_reason,
        intake_channel=complaint.intake_channel,
        submitted_at=complaint.submitted_at,
        resolved_reported_at=complaint.resolved_reported_at,
        closed_at=complaint.closed_at,
        updated_at=complaint.updated_at,
        active_incident_id=active_inc_id,
        active_incident_number=active_inc_num,
        status_history=history_resp,
        confirmations=conf_resp,
    )


@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
async def create_complaint(
    data: ComplaintCreate,
    request: Request,
    idempotency_key: Optional[str] = Header(None),
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)

    # Check Idempotency Key (AT-04)
    if idempotency_key:
        cached_stmt = select(Complaint).where(
            Complaint.description == data.description,
            Complaint.property_id == data.property_id,
            Complaint.category_id == data.category_id,
        ).order_by(desc(Complaint.submitted_at))
        cached_res = await db.execute(cached_stmt)
        existing = cached_res.scalars().first()
        if existing:
            detail = await get_complaint_detail(db, existing.id, profile)
            return build_complaint_response(detail)

    if profile.role == "resident":
        res_stmt = select(Resident).where(Resident.profile_id == profile.id)
        res_exec = await db.execute(res_stmt)
        resident = res_exec.scalars().first()
        if not resident or resident.verification_status != "verified":
            raise ForbiddenError("Resident account is awaiting office verification.")

        complaint = await create_resident_complaint(db, data, resident, profile, request_id)
    elif profile.role in ("complaint_officer", "administrator"):
        # Officer/admin standard submission requires offline data or specific resident
        raise ForbiddenError("Use /complaints/offline for officer walk-in/phone intake.")
    else:
        raise ForbiddenError("Staff roles cannot submit complaints.")

    detail = await get_complaint_detail(db, complaint.id, profile)
    return build_complaint_response(detail)


@router.post("/offline", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
async def create_offline_complaint_endpoint(
    data: OfflineComplaintCreate,
    request: Request,
    profile: Profile = Depends(require_role("complaint_officer", "administrator")),
    db: AsyncSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    complaint = await create_offline_complaint(db, data, profile, request_id)
    detail = await get_complaint_detail(db, complaint.id, profile)
    return build_complaint_response(detail)


@router.get("", response_model=PaginatedResponse[ComplaintResponse])
async def list_complaints(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    category_id: Optional[uuid.UUID] = Query(None),
    is_urgent: Optional[bool] = Query(None),
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
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
    )

    # Scoping for resident role
    if profile.role == "resident":
        res_stmt = select(Resident).where(Resident.profile_id == profile.id)
        res_exec = await db.execute(res_stmt)
        resident = res_exec.scalars().first()
        if not resident:
            return PaginatedResponse(items=[], total=0, page=page, page_size=page_size, pages=0)
        stmt = stmt.where(Complaint.resident_id == resident.id)

    if status_filter:
        stmt = stmt.where(Complaint.status == status_filter)
    if category_id:
        stmt = stmt.where(Complaint.category_id == category_id)
    if is_urgent is not None:
        stmt = stmt.where(Complaint.is_urgent == is_urgent)

    # Total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar_one()

    # Pagination & Ordering
    stmt = stmt.order_by(desc(Complaint.submitted_at)).offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(stmt)
    complaints = res.scalars().all()

    items = [build_complaint_response(c) for c in complaints]
    pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(
    complaint_id: uuid.UUID,
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    resident = None
    if profile.role == "resident":
        r_stmt = select(Resident).where(Resident.profile_id == profile.id)
        r_res = await db.execute(r_stmt)
        resident = r_res.scalars().first()

    complaint = await get_complaint_detail(db, complaint_id, profile, resident)
    return build_complaint_response(complaint)


@router.post("/{complaint_id}/confirmations", response_model=ComplaintResponse)
async def submit_confirmation(
    complaint_id: uuid.UUID,
    data: ResolutionConfirmationCreate,
    request: Request,
    resident: Resident = Depends(get_current_resident),
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    complaint = await submit_resident_confirmation(db, complaint_id, data, resident, profile, request_id)
    detail = await get_complaint_detail(db, complaint.id, profile, resident)
    return build_complaint_response(detail)
