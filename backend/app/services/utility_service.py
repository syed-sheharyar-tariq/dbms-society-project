import datetime
import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError, ConflictError, NotFoundError
from app.models.entities import (
    Incident,
    Profile,
    UtilityCase,
    UtilityCaseUpdate,
    UtilityCompany,
)
from app.schemas.utility_schemas import UtilityCaseCreate, UtilityCaseUpdateCreate
from app.services.audit_service import log_audit_event


async def create_utility_case(
    db: AsyncSession,
    incident_id: uuid.UUID,
    data: UtilityCaseCreate,
    officer_profile: Profile,
    request_id: Optional[str] = None,
) -> UtilityCase:
    incident = await db.get(Incident, incident_id)
    if not incident:
        raise NotFoundError("Incident not found.")

    utility = await db.get(UtilityCompany, data.utility_company_id)
    if not utility or not utility.is_active:
        raise BadRequestError("Referenced utility company is inactive or not found.")

    # Check external reference uniqueness if provided
    if data.external_reference_number:
        ref_check = await db.execute(
            select(UtilityCase).where(
                UtilityCase.utility_company_id == data.utility_company_id,
                UtilityCase.external_reference_number == data.external_reference_number,
            )
        )
        if ref_check.scalars().first():
            raise ConflictError(
                f"External reference '{data.external_reference_number}' is already registered for {utility.name}."
            )

    now = datetime.datetime.now(datetime.timezone.utc)
    utility_case = UtilityCase(
        incident_id=incident.id,
        utility_company_id=data.utility_company_id,
        external_reference_number=data.external_reference_number,
        status="submitted",
        submitted_at=now,
        expected_resolution_at=data.expected_resolution_at,
        created_by=officer_profile.id,
        created_at=now,
    )
    db.add(utility_case)
    await db.flush()

    # Initial update
    db.add(
        UtilityCaseUpdate(
            utility_case_id=utility_case.id,
            actor_profile_id=officer_profile.id,
            direction="outbound",
            update_type="case_lodged",
            message=data.notes or f"Fault case lodged with {utility.name}",
            recorded_at=now,
        )
    )

    incident.routing_type = "external"
    if incident.status in ("open", "triaged"):
        incident.status = "awaiting_external"

    await log_audit_event(
        db,
        action="CREATE_UTILITY_CASE",
        entity_type="utility_cases",
        entity_id=utility_case.id,
        actor_profile_id=officer_profile.id,
        request_id=request_id,
        new_values={
            "utility_company": utility.name,
            "external_ref": data.external_reference_number,
        },
    )

    await db.commit()
    await db.refresh(utility_case)
    return utility_case


async def add_utility_case_update(
    db: AsyncSession,
    case_id: uuid.UUID,
    data: UtilityCaseUpdateCreate,
    officer_profile: Profile,
    request_id: Optional[str] = None,
) -> UtilityCaseUpdate:
    """Appends an external communication or provider follow-up (AT-12)."""
    case = await db.get(UtilityCase, case_id)
    if not case:
        raise NotFoundError("Utility case not found.")

    now = datetime.datetime.now(datetime.timezone.utc)

    # First response tracking
    if data.direction == "inbound" and case.first_response_at is None:
        case.first_response_at = data.provider_event_at or now

    update = UtilityCaseUpdate(
        utility_case_id=case.id,
        actor_profile_id=officer_profile.id,
        direction=data.direction,
        update_type=data.update_type,
        message=data.message,
        provider_event_at=data.provider_event_at,
        attachment_path=data.attachment_path,
        recorded_at=now,
    )
    db.add(update)

    await log_audit_event(
        db,
        action="ADD_UTILITY_UPDATE",
        entity_type="utility_case_updates",
        entity_id=update.id,
        actor_profile_id=officer_profile.id,
        request_id=request_id,
        new_values={"direction": data.direction, "update_type": data.update_type},
    )

    await db.commit()
    await db.refresh(update)
    return update
