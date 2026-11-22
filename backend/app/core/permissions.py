import datetime
import uuid
from datetime import date
from typing import Callable, Optional
from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import verify_supabase_jwt
from app.database import get_db
from app.models.entities import Profile, Property, PropertyResident, Resident


async def get_token_auth_header(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise UnauthorizedError("Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError("Invalid Authorization header format. Expected 'Bearer <token>'")
    return parts[1]


async def get_current_token_payload(token: str = Depends(get_token_auth_header)) -> dict:
    return verify_supabase_jwt(token)


async def get_current_auth_user_id(payload: dict = Depends(get_current_token_payload)) -> uuid.UUID:
    sub = payload.get("sub")
    if not sub:
        raise UnauthorizedError("Token missing subject claim")
    try:
        return uuid.UUID(sub)
    except ValueError:
        raise UnauthorizedError("Malformed subject identifier in token")



DEMO_SEEDS = {
    uuid.UUID("a1111111-1111-1111-1111-111111111111"): {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
        "role": "resident",
        "full_name": "Fahad Resident (Flat A-204)",
        "phone": "+92-300-1234567",
        "email": "resident@jauhar.com",
    },
    uuid.UUID("a2222222-2222-2222-2222-222222222222"): {
        "id": uuid.UUID("22222222-2222-2222-2222-222222222222"),
        "role": "complaint_officer",
        "full_name": "Tariq Mehmood (Complaint Officer)",
        "phone": "+92-300-7654321",
        "email": "officer@jauhar.com",
    },
    uuid.UUID("a3333333-3333-3333-3333-333333333333"): {
        "id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
        "role": "field_staff",
        "full_name": "Imran Khan (Society Electrician)",
        "phone": "+92-321-9876543",
        "email": "staff@jauhar.com",
    },
    uuid.UUID("a4444444-4444-4444-4444-444444444444"): {
        "id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
        "role": "administrator",
        "full_name": "Society Administrator",
        "phone": "+92-333-5555555",
        "email": "admin@jauhar.com",
    },
}


async def get_current_profile(
    auth_user_id: uuid.UUID = Depends(get_current_auth_user_id),
    payload: dict = Depends(get_current_token_payload),
    db: AsyncSession = Depends(get_db),
) -> Profile:
    stmt = select(Profile).where(Profile.auth_user_id == auth_user_id)
    result = await db.execute(stmt)
    profile = result.scalars().first()

    if not profile and auth_user_id in DEMO_SEEDS:
        demo = DEMO_SEEDS[auth_user_id]
        profile = Profile(
            id=demo["id"],
            auth_user_id=auth_user_id,
            role=demo["role"],
            full_name=demo["full_name"],
            phone=demo["phone"],
            email=demo["email"],
            is_active=True,
        )
        db.add(profile)
        await db.flush()

        if profile.role == "resident":
            res_id = uuid.UUID("55555555-5555-5555-5555-555555555555")
            r_res = await db.execute(select(Resident).where(Resident.id == res_id))
            resident = r_res.scalars().first()
            if not resident:
                resident = Resident(
                    id=res_id,
                    profile_id=profile.id,
                    verification_status="verified",
                )
                db.add(resident)
                await db.flush()

            # Ensure at least one property association
            assoc_res = await db.execute(select(PropertyResident).where(PropertyResident.resident_id == resident.id))
            if not assoc_res.scalars().first():
                prop_res = await db.execute(select(Property).limit(1))
                prop = prop_res.scalars().first()
                if prop:
                    assoc = PropertyResident(
                        resident_id=resident.id,
                        property_id=prop.id,
                        relationship_type="owner",
                        valid_from=date.today(),
                        is_primary_contact=True,
                    )
                    db.add(assoc)

        await db.commit()
        await db.refresh(profile)

    elif not profile:
        # Dynamic auto-provisioning for authenticated Supabase users
        token_email = payload.get("email") or f"user_{str(auth_user_id)[:8]}@society.com"
        meta = payload.get("user_metadata") or {}
        user_name = meta.get("full_name") or meta.get("name") or token_email.split("@")[0].capitalize()
        user_role = meta.get("role", "resident")
        if user_role not in ("administrator", "complaint_officer", "field_staff", "resident"):
            user_role = "resident"

        profile = Profile(
            id=uuid.uuid4(),
            auth_user_id=auth_user_id,
            role=user_role,
            full_name=user_name,
            phone=meta.get("phone"),
            email=token_email,
            is_active=True,
        )
        db.add(profile)
        await db.flush()

        if profile.role == "resident":
            res_id = uuid.uuid4()
            resident = Resident(
                id=res_id,
                profile_id=profile.id,
                verification_status="verified",
                verified_at=datetime.datetime.now(datetime.timezone.utc),
            )
            db.add(resident)
            await db.flush()

            # Link to first property by default if none associated yet
            prop_res = await db.execute(select(Property).limit(1))
            prop = prop_res.scalars().first()
            if prop:
                assoc = PropertyResident(
                    resident_id=resident.id,
                    property_id=prop.id,
                    relationship_type="owner",
                    valid_from=date.today(),
                    is_primary_contact=True,
                )
                db.add(assoc)

        await db.commit()
        await db.refresh(profile)

    if not profile:
        raise UnauthorizedError("User profile does not exist in the CMS")
    if not profile.is_active:
        raise ForbiddenError("User account has been deactivated")

    return profile


def require_role(*allowed_roles: str) -> Callable:
    async def role_checker(profile: Profile = Depends(get_current_profile)) -> Profile:
        if profile.role not in allowed_roles:
            raise ForbiddenError(f"Access restricted to roles: {', '.join(allowed_roles)}")
        return profile

    return role_checker


async def get_current_resident(
    profile: Profile = Depends(require_role("resident")),
    db: AsyncSession = Depends(get_db),
) -> Resident:
    stmt = select(Resident).where(Resident.profile_id == profile.id)
    result = await db.execute(stmt)
    resident = result.scalars().first()

    if not resident:
        raise ForbiddenError("Resident profile not found")
    if resident.verification_status != "verified":
        raise ForbiddenError("Resident account is awaiting management office verification")

    return resident


async def check_property_authorization(
    db: AsyncSession,
    resident_id: uuid.UUID,
    property_id: uuid.UUID,
) -> bool:
    """Verifies that the resident has an active association with the given property."""
    today = date.today()
    stmt = (
        select(PropertyResident)
        .where(
            PropertyResident.resident_id == resident_id,
            PropertyResident.property_id == property_id,
            PropertyResident.valid_from <= today,
            (PropertyResident.valid_until.is_(None) | (PropertyResident.valid_until >= today)),
        )
    )
    result = await db.execute(stmt)
    assoc = result.scalars().first()
    return assoc is not None
