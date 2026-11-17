import datetime
import math
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError
from app.core.permissions import require_role
from app.database import get_db
from app.models.entities import (
    AuditLog,
    Profile,
    Property,
    PropertyResident,
    Resident,
)
from app.schemas.common import PaginatedResponse
from app.schemas.profile_schemas import ProfileResponse
from app.schemas.report_schemas import AuditLogResponse
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/admin", tags=["Administration"])


class VerifyResidentRequest(BaseModel):
    verification_status: str = Field(..., description="verified or rejected")


class CreatePropertyResidentAssociation(BaseModel):
    resident_id: uuid.UUID
    property_id: uuid.UUID
    relationship_type: str = Field(..., description="owner, tenant, family_member, authorized_occupant, other")
    valid_from: datetime.date
    valid_until: Optional[datetime.date] = None
    is_primary_contact: bool = False


class UpdateUserRoleRequest(BaseModel):
    role: str = Field(..., description="administrator, complaint_officer, field_staff, resident")


@router.get("/users", response_model=PaginatedResponse[ProfileResponse])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    role: Optional[str] = Query(None),
    admin: Profile = Depends(require_role("administrator", "complaint_officer")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Profile)
    if role:
        stmt = stmt.where(Profile.role == role)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar_one()

    stmt = stmt.order_by(desc(Profile.created_at)).offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(stmt)
    profiles = res.scalars().all()

    items = [ProfileResponse.model_validate(p) for p in profiles]
    pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("/residents/{resident_id}/verify")
async def verify_resident(
    resident_id: uuid.UUID,
    data: VerifyResidentRequest,
    request: Request,
    admin: Profile = Depends(require_role("administrator", "complaint_officer")),
    db: AsyncSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    resident = await db.get(Resident, resident_id)
    if not resident:
        res = await db.execute(select(Resident).where(Resident.profile_id == resident_id))
        resident = res.scalars().first()
    if not resident:
        raise NotFoundError("Resident not found.")

    old_status = resident.verification_status
    resident.verification_status = data.verification_status
    resident.verified_by = admin.id
    resident.verified_at = datetime.datetime.now(datetime.timezone.utc)

    await log_audit_event(
        db,
        action="VERIFY_RESIDENT",
        entity_type="residents",
        entity_id=resident.id,
        actor_profile_id=admin.id,
        request_id=request_id,
        old_values={"verification_status": old_status},
        new_values={"verification_status": data.verification_status},
    )

    await db.commit()
    return {"status": "success", "resident_id": str(resident.id), "verification_status": data.verification_status}


@router.post("/property-residents", status_code=status.HTTP_201_CREATED)
async def associate_property_resident(
    data: CreatePropertyResidentAssociation,
    request: Request,
    admin: Profile = Depends(require_role("administrator", "complaint_officer")),
    db: AsyncSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    resident = await db.get(Resident, data.resident_id)
    if not resident:
        res = await db.execute(select(Resident).where(Resident.profile_id == data.resident_id))
        resident = res.scalars().first()
    if not resident:
        raise NotFoundError("Resident not found.")

    prop = await db.get(Property, data.property_id)
    if not prop:
        raise NotFoundError("Property not found.")

    assoc = PropertyResident(
        resident_id=data.resident_id,
        property_id=data.property_id,
        relationship_type=data.relationship_type,
        valid_from=data.valid_from,
        valid_until=data.valid_until,
        is_primary_contact=data.is_primary_contact,
    )
    db.add(assoc)

    await log_audit_event(
        db,
        action="ASSOCIATE_PROPERTY_RESIDENT",
        entity_type="property_residents",
        entity_id=assoc.id,
        actor_profile_id=admin.id,
        request_id=request_id,
        new_values={
            "resident_id": str(data.resident_id),
            "property_id": str(data.property_id),
            "relationship_type": data.relationship_type,
        },
    )

    await db.commit()
    return {"status": "success", "association_id": str(assoc.id)}


@router.patch("/users/{profile_id}/role")
async def update_user_role(
    profile_id: uuid.UUID,
    data: UpdateUserRoleRequest,
    request: Request,
    admin: Profile = Depends(require_role("administrator")),
    db: AsyncSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    target = await db.get(Profile, profile_id)
    if not target:
        raise NotFoundError("User profile not found.")

    old_role = target.role
    target.role = data.role

    await log_audit_event(
        db,
        action="UPDATE_USER_ROLE",
        entity_type="profiles",
        entity_id=target.id,
        actor_profile_id=admin.id,
        request_id=request_id,
        old_values={"role": old_role},
        new_values={"role": data.role},
    )

    await db.commit()
    return {"status": "success", "profile_id": str(target.id), "new_role": data.role}


@router.get("/audit-logs", response_model=PaginatedResponse[AuditLogResponse])
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    entity_type: Optional[str] = Query(None),
    admin: Profile = Depends(require_role("administrator")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AuditLog).options(selectinload(AuditLog.actor))
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar_one()

    stmt = stmt.order_by(desc(AuditLog.created_at)).offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(stmt)
    logs = res.scalars().all()

    items = []
    for log_entry in logs:
        items.append(
            AuditLogResponse(
                id=log_entry.id,
                actor_profile_id=log_entry.actor_profile_id,
                actor_name=log_entry.actor.full_name if log_entry.actor else "System",
                action=log_entry.action,
                entity_type=log_entry.entity_type,
                entity_id=log_entry.entity_id,
                request_id=log_entry.request_id,
                old_values=log_entry.old_values,
                new_values=log_entry.new_values,
                created_at=log_entry.created_at,
            )
        )
    pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
