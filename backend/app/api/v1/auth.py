import datetime
import uuid
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import BadRequestError, ForbiddenError
from app.core.permissions import get_current_profile, verify_supabase_jwt
from app.database import get_db
from app.models.entities import Block, Profile, Property, PropertyResident, Resident
from app.schemas.profile_schemas import (
    MeResponse,
    ProfileResponse,
    ProfileUpdate,
    RegisterProfileRequest,
    ResidentResponse,
)
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="", tags=["Auth & Profiles"])


@router.post("/auth/register-profile", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def register_profile(
    data: RegisterProfileRequest,
    request: Request,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)

    # Determine auth_user_id from bearer token or request body
    auth_user_id = data.auth_user_id
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            try:
                payload = verify_supabase_jwt(parts[1])
                sub = payload.get("sub")
                if sub:
                    auth_user_id = uuid.UUID(sub)
                if not data.email and payload.get("email"):
                    data.email = payload.get("email")
            except Exception:
                pass

    if not auth_user_id:
        auth_user_id = uuid.uuid4()

    # Validate role
    role = data.role.lower()
    if role not in ("administrator", "complaint_officer", "field_staff", "resident"):
        raise BadRequestError(f"Invalid role: {role}")

    if role == "administrator":
        if data.admin_passcode != "society-admin-2026":
            raise ForbiddenError("Invalid administrator security passcode.")

    # Format full name with trade specialization if field staff
    formatted_name = data.full_name.strip()
    if role == "field_staff" and data.trade_specialization:
        trade_suffix = f"({data.trade_specialization.strip()})"
        if trade_suffix not in formatted_name:
            formatted_name = f"{formatted_name} {trade_suffix}"

    # Check if profile already exists by auth_user_id or email
    stmt = select(Profile).where((Profile.auth_user_id == auth_user_id) | ((Profile.email == data.email) if data.email else False))
    res = await db.execute(stmt)
    profile = res.scalars().first()

    now = datetime.datetime.now(datetime.timezone.utc)
    if profile:
        profile.full_name = formatted_name
        if data.phone:
            profile.phone = data.phone
        profile.role = role
        profile.auth_user_id = auth_user_id
    else:
        profile = Profile(
            id=uuid.uuid4(),
            auth_user_id=auth_user_id,
            role=role,
            full_name=formatted_name,
            phone=data.phone,
            email=data.email,
            is_active=True,
        )
        db.add(profile)
        await db.flush()

    # If Resident, ensure Resident record & Property association exist
    if role == "resident":
        r_stmt = select(Resident).where(Resident.profile_id == profile.id)
        r_res = await db.execute(r_stmt)
        resident = r_res.scalars().first()
        if not resident:
            resident = Resident(
                id=uuid.uuid4(),
                profile_id=profile.id,
                verification_status="verified",
                verified_at=now,
            )
            db.add(resident)
            await db.flush()
        else:
            # Auto-verify resident for seamless testing experience
            resident.verification_status = "verified"
            resident.verified_at = now

        target_prop_id = data.property_id

        # If resident requested a new property unit
        if not target_prop_id and data.new_property_number and data.block_id:
            prop_check = await db.execute(
                select(Property).where(
                    Property.block_id == data.block_id,
                    Property.property_number == data.new_property_number.strip().upper(),
                )
            )
            existing_prop = prop_check.scalars().first()
            if existing_prop:
                target_prop_id = existing_prop.id
            else:
                new_prop = Property(
                    id=uuid.uuid4(),
                    block_id=data.block_id,
                    property_number=data.new_property_number.strip().upper(),
                    property_type="house",
                    address_note="Registered during resident signup",
                    is_active=True,
                )
                db.add(new_prop)
                await db.flush()
                target_prop_id = new_prop.id

        # Fallback to first available property if none specified
        if not target_prop_id:
            first_prop_res = await db.execute(select(Property).limit(1))
            first_prop = first_prop_res.scalars().first()
            if first_prop:
                target_prop_id = first_prop.id

        if target_prop_id:
            assoc_check = await db.execute(
                select(PropertyResident).where(
                    PropertyResident.resident_id == resident.id,
                    PropertyResident.property_id == target_prop_id,
                )
            )
            if not assoc_check.scalars().first():
                assoc = PropertyResident(
                    id=uuid.uuid4(),
                    resident_id=resident.id,
                    property_id=target_prop_id,
                    relationship_type=data.relationship_type or "owner",
                    valid_from=date.today(),
                    is_primary_contact=True,
                )
                db.add(assoc)

    await log_audit_event(
        db,
        action="REGISTER_PROFILE",
        entity_type="profiles",
        entity_id=profile.id,
        actor_profile_id=profile.id,
        request_id=request_id,
        new_values={"role": role, "full_name": formatted_name, "email": data.email},
    )

    await db.commit()
    await db.refresh(profile)
    return ProfileResponse.model_validate(profile)


@router.get("/me", response_model=MeResponse)

async def get_me(
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    resident_data = None
    if profile.role == "resident":
        stmt = (
            select(Resident)
            .options(
                selectinload(Resident.property_associations)
                .selectinload(PropertyResident.property)
                .selectinload(Property.block)
            )
            .where(Resident.profile_id == profile.id)
        )
        res = await db.execute(stmt)
        resident = res.scalars().first()
        if resident:
            assoc_list = []
            for assoc in resident.property_associations:
                block_code_str = (
                    assoc.property.block.code
                    if assoc.property and assoc.property.block
                    else str(assoc.property.block_id)
                )
                assoc_list.append({
                    "property_id": assoc.property_id,
                    "property_number": assoc.property.property_number,
                    "block_code": block_code_str,
                    "relationship_type": assoc.relationship_type,
                    "is_primary_contact": assoc.is_primary_contact,
                    "valid_from": assoc.valid_from,
                    "valid_until": assoc.valid_until,
                })

            resident_data = ResidentResponse(
                id=resident.id,
                profile_id=resident.profile_id,
                verification_status=resident.verification_status,
                verified_at=resident.verified_at,
                properties=assoc_list,
            )

    return MeResponse(
        profile=ProfileResponse.model_validate(profile),
        resident=resident_data,
    )


@router.patch("/me", response_model=ProfileResponse)
async def update_me(
    data: ProfileUpdate,
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    # Role cannot be updated by user (AT-20)
    if data.full_name is not None:
        profile.full_name = data.full_name
    if data.phone is not None:
        profile.phone = data.phone

    await db.commit()
    await db.refresh(profile)
    return ProfileResponse.model_validate(profile)
