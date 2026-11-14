from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.permissions import get_current_profile
from app.database import get_db
from app.models.entities import Profile, PropertyResident, Resident
from app.schemas.profile_schemas import MeResponse, ProfileResponse, ProfileUpdate, ResidentResponse

router = APIRouter(prefix="", tags=["Auth & Profiles"])


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
                selectinload(Resident.property_associations).selectinload(PropertyResident.property)
            )
            .where(Resident.profile_id == profile.id)
        )
        res = await db.execute(stmt)
        resident = res.scalars().first()
        if resident:
            assoc_list = []
            for assoc in resident.property_associations:
                assoc_list.append({
                    "property_id": assoc.property_id,
                    "property_number": assoc.property.property_number,
                    "block_code": assoc.property.block_id,
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
