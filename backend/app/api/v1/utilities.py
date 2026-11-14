import datetime
import math
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.permissions import require_role
from app.database import get_db
from app.models.entities import (
    Profile,
    UtilityCase,
    UtilityCaseUpdate,
    UtilityCompany,
)
from app.schemas.common import PaginatedResponse
from app.schemas.utility_schemas import (
    UtilityCaseCreate,
    UtilityCaseResponse,
    UtilityCaseUpdateCreate,
    UtilityCaseUpdateResponse,
    UtilityCompanyResponse,
)
from app.services.utility_service import (
    add_utility_case_update,
    create_utility_case,
)

router = APIRouter(tags=["External Utilities"])


def build_utility_case_response(case: UtilityCase) -> UtilityCaseResponse:
    now = datetime.datetime.now(datetime.timezone.utc)
    is_overdue = (
        case.expected_resolution_at is not None
        and case.expected_resolution_at < now
        and case.status not in ("resolved", "closed", "cancelled")
    )

    updates_resp = []
    if case.updates:
        for u in case.updates:
            updates_resp.append(
                UtilityCaseUpdateResponse(
                    id=u.id,
                    utility_case_id=u.utility_case_id,
                    actor_profile_id=u.actor_profile_id,
                    actor_name=u.actor.full_name if u.actor else None,
                    direction=u.direction,
                    update_type=u.update_type,
                    message=u.message,
                    provider_event_at=u.provider_event_at,
                    recorded_at=u.recorded_at,
                    attachment_path=u.attachment_path,
                )
            )

    return UtilityCaseResponse(
        id=case.id,
        incident_id=case.incident_id,
        incident_number=case.incident.incident_number if case.incident else None,
        utility_company_id=case.utility_company_id,
        utility_company_name=case.utility_company.name if case.utility_company else None,
        external_reference_number=case.external_reference_number,
        status=case.status,
        submitted_at=case.submitted_at,
        expected_resolution_at=case.expected_resolution_at,
        first_response_at=case.first_response_at,
        resolved_at=case.resolved_at,
        created_by=case.created_by,
        created_at=case.created_at,
        updated_at=case.updated_at,
        is_overdue=is_overdue,
        updates=updates_resp,
    )


@router.get("/utilities/companies", response_model=List[UtilityCompanyResponse])
async def list_utility_companies(
    db: AsyncSession = Depends(get_db),
    active_only: bool = True,
):
    stmt = select(UtilityCompany)
    if active_only:
        stmt = stmt.where(UtilityCompany.is_active.is_(True))
    stmt = stmt.order_by(UtilityCompany.name)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/incidents/{incident_id}/utility-cases", response_model=UtilityCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_utility_case_endpoint(
    incident_id: uuid.UUID,
    data: UtilityCaseCreate,
    request: Request,
    profile: Profile = Depends(require_role("complaint_officer", "administrator")),
    db: AsyncSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    case = await create_utility_case(db, incident_id, data, profile, request_id)
    
    stmt = (
        select(UtilityCase)
        .options(
            selectinload(UtilityCase.incident),
            selectinload(UtilityCase.utility_company),
            selectinload(UtilityCase.updates).selectinload(UtilityCaseUpdate.actor),
        )
        .where(UtilityCase.id == case.id)
    )
    res = await db.execute(stmt)
    return build_utility_case_response(res.scalars().first())


@router.get("/utility-cases", response_model=PaginatedResponse[UtilityCaseResponse])
async def list_utility_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    utility_company_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    overdue_only: bool = False,
    profile: Profile = Depends(require_role("complaint_officer", "administrator")),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.datetime.now(datetime.timezone.utc)
    stmt = (
        select(UtilityCase)
        .options(
            selectinload(UtilityCase.incident),
            selectinload(UtilityCase.utility_company),
            selectinload(UtilityCase.updates).selectinload(UtilityCaseUpdate.actor),
        )
    )

    if utility_company_id:
        stmt = stmt.where(UtilityCase.utility_company_id == utility_company_id)
    if status_filter:
        stmt = stmt.where(UtilityCase.status == status_filter)
    if overdue_only:
        stmt = stmt.where(
            UtilityCase.expected_resolution_at.is_not(None),
            UtilityCase.expected_resolution_at < now,
            UtilityCase.status.not_in(["resolved", "closed", "cancelled"]),
        )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar_one()

    stmt = stmt.order_by(desc(UtilityCase.submitted_at)).offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(stmt)
    cases = res.scalars().all()

    items = [build_utility_case_response(c) for c in cases]
    pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("/utility-cases/{case_id}/updates", response_model=UtilityCaseUpdateResponse, status_code=status.HTTP_201_CREATED)
async def add_update(
    case_id: uuid.UUID,
    data: UtilityCaseUpdateCreate,
    request: Request,
    profile: Profile = Depends(require_role("complaint_officer", "administrator")),
    db: AsyncSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    update = await add_utility_case_update(db, case_id, data, profile, request_id)
    return UtilityCaseUpdateResponse.model_validate(update)
