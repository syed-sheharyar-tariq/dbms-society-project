import math
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.permissions import require_role
from app.database import get_db
from app.models.entities import (
    Incident,
    IncidentComplaintLink,
    Profile,
)
from app.schemas.common import PaginatedResponse
from app.schemas.incident_schemas import (
    IncidentComplaintLinkResponse,
    IncidentCreate,
    IncidentLinkCreate,
    IncidentResponse,
    IncidentStatusUpdate,
    IncidentUnlinkRequest,
)
from app.services.incident_service import (
    create_incident,
    link_complaint_to_incident,
    unlink_complaint_from_incident,
    update_incident_status,
)

router = APIRouter(prefix="/incidents", tags=["Incidents"])


def build_incident_response(incident: Incident) -> IncidentResponse:
    active_complaints = []
    if incident.complaint_links:
        for link in incident.complaint_links:
            if link.unlinked_at is None and link.complaint:
                c = link.complaint
                active_complaints.append({
                    "id": c.id,
                    "complaint_number": c.complaint_number,
                    "status": c.status,
                    "description": c.description,
                    "is_urgent": c.is_urgent,
                    "property_id": c.property_id,
                    "link_id": link.id,
                })

    return IncidentResponse(
        id=incident.id,
        incident_number=incident.incident_number,
        category_id=incident.category_id,
        category_name=incident.category.name if incident.category else None,
        title=incident.title,
        description=incident.description,
        status=incident.status,
        routing_type=incident.routing_type,
        priority=incident.priority,
        area_description=incident.area_description,
        created_at=incident.created_at,
        resolved_at=incident.resolved_at,
        closed_at=incident.closed_at,
        updated_at=incident.updated_at,
        linked_complaint_count=len(active_complaints),
        active_complaints=active_complaints,
    )


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident_endpoint(
    data: IncidentCreate,
    request: Request,
    profile: Profile = Depends(require_role("complaint_officer", "administrator")),
    db: AsyncSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    incident = await create_incident(db, data, profile, request_id)
    # Reload with relationships
    stmt = (
        select(Incident)
        .options(
            selectinload(Incident.category),
            selectinload(Incident.complaint_links).selectinload(IncidentComplaintLink.complaint),
        )
        .where(Incident.id == incident.id)
    )
    res = await db.execute(stmt)
    full_inc = res.scalars().first()
    return build_incident_response(full_inc)


@router.get("", response_model=PaginatedResponse[IncidentResponse])
async def list_incidents(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    category_id: Optional[uuid.UUID] = Query(None),
    priority: Optional[str] = Query(None),
    profile: Profile = Depends(require_role("complaint_officer", "administrator", "field_staff")),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Incident)
        .options(
            selectinload(Incident.category),
            selectinload(Incident.complaint_links).selectinload(IncidentComplaintLink.complaint),
        )
    )

    if status_filter:
        stmt = stmt.where(Incident.status == status_filter)
    if category_id:
        stmt = stmt.where(Incident.category_id == category_id)
    if priority:
        stmt = stmt.where(Incident.priority == priority)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar_one()

    stmt = stmt.order_by(desc(Incident.created_at)).offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(stmt)
    incidents = res.scalars().all()

    items = [build_incident_response(i) for i in incidents]
    pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: uuid.UUID,
    profile: Profile = Depends(require_role("complaint_officer", "administrator", "field_staff")),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Incident)
        .options(
            selectinload(Incident.category),
            selectinload(Incident.complaint_links).selectinload(IncidentComplaintLink.complaint),
        )
        .where(Incident.id == incident_id)
    )
    res = await db.execute(stmt)
    incident = res.scalars().first()
    return build_incident_response(incident)


@router.patch("/{incident_id}/status", response_model=IncidentResponse)
async def patch_incident_status(
    incident_id: uuid.UUID,
    data: IncidentStatusUpdate,
    request: Request,
    profile: Profile = Depends(require_role("complaint_officer", "administrator")),
    db: AsyncSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    incident = await update_incident_status(db, incident_id, data.status, data.reason, profile, request_id)
    
    stmt = (
        select(Incident)
        .options(
            selectinload(Incident.category),
            selectinload(Incident.complaint_links).selectinload(IncidentComplaintLink.complaint),
        )
        .where(Incident.id == incident.id)
    )
    res = await db.execute(stmt)
    full_inc = res.scalars().first()
    return build_incident_response(full_inc)


@router.post("/{incident_id}/links", response_model=IncidentComplaintLinkResponse, status_code=status.HTTP_201_CREATED)
async def link_complaint(
    incident_id: uuid.UUID,
    data: IncidentLinkCreate,
    request: Request,
    profile: Profile = Depends(require_role("complaint_officer", "administrator")),
    db: AsyncSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    link = await link_complaint_to_incident(db, incident_id, data, profile, request_id)
    return IncidentComplaintLinkResponse.model_validate(link)


@router.delete("/{incident_id}/links/{link_id}", response_model=IncidentComplaintLinkResponse)
async def unlink_complaint(
    incident_id: uuid.UUID,
    link_id: uuid.UUID,
    data: IncidentUnlinkRequest,
    request: Request,
    profile: Profile = Depends(require_role("complaint_officer", "administrator")),
    db: AsyncSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    link = await unlink_complaint_from_incident(db, link_id, data.unlink_reason, profile, request_id)
    return IncidentComplaintLinkResponse.model_validate(link)
