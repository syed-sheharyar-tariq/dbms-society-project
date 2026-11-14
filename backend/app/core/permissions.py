import uuid
from datetime import date
from typing import Callable, Optional
from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import verify_supabase_jwt
from app.database import get_db
from app.models.entities import Profile, PropertyResident, Resident


async def get_token_auth_header(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise UnauthorizedError("Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError("Invalid Authorization header format. Expected 'Bearer <token>'")
    return parts[1]


async def get_current_auth_user_id(token: str = Depends(get_token_auth_header)) -> uuid.UUID:
    payload = verify_supabase_jwt(token)
    sub = payload.get("sub")
    if not sub:
        raise UnauthorizedError("Token missing subject claim")
    try:
        return uuid.UUID(sub)
    except ValueError:
        raise UnauthorizedError("Malformed subject identifier in token")


async def get_current_profile(
    auth_user_id: uuid.UUID = Depends(get_current_auth_user_id),
    db: AsyncSession = Depends(get_db),
) -> Profile:
    stmt = select(Profile).where(Profile.auth_user_id == auth_user_id)
    result = await db.execute(stmt)
    profile = result.scalars().first()

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
