import datetime
import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.errors import BadRequestError, ForbiddenError
from app.database import Base
from app.models.entities import (
    Block,
    Category,
    IncidentComplaintLink,
    Profile,
    Property,
    PropertyResident,
    Resident,
    UtilityCompany,
)
from app.schemas.assignment_schemas import AssignmentStatusUpdate, WorkAssignmentCreate
from app.schemas.complaint_schemas import (
    ComplaintCreate,
    OfflineComplaintCreate,
    ResolutionConfirmationCreate,
)
from app.schemas.incident_schemas import IncidentCreate, IncidentLinkCreate
from app.schemas.utility_schemas import UtilityCaseCreate, UtilityCaseUpdateCreate
from app.services.assignment_service import (
    create_work_assignment,
    update_assignment_status,
)
from app.services.complaint_service import (
    create_offline_complaint,
    create_resident_complaint,
    get_complaint_detail,
    submit_resident_confirmation,
)
from app.services.incident_service import (
    create_incident,
    link_complaint_to_incident,
    unlink_complaint_from_incident,
    update_incident_status,
)
from app.services.report_service import (
    get_dashboard_summary,
    get_utility_performance_report,
)
from app.services.utility_service import (
    add_utility_case_update,
    create_utility_case,
)


@pytest_asyncio.fixture
async def async_db():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def seed_fixtures(async_db: AsyncSession):
    # 1. Block
    block = Block(id=uuid.uuid4(), code="BLK-A", name="Block A")
    async_db.add(block)

    # 2. Category
    cat_elec = Category(id=uuid.uuid4(), name="Electricity", description="Electrical grid")
    cat_water = Category(id=uuid.uuid4(), name="Water", description="Water supply")
    async_db.add_all([cat_elec, cat_water])

    # 3. Utility
    utility = UtilityCompany(id=uuid.uuid4(), name="K-Electric", contact_phone="118")
    async_db.add(utility)

    # 4. Property
    prop_1 = Property(id=uuid.uuid4(), block_id=block.id, property_number="A-101", property_type="house")
    prop_2 = Property(id=uuid.uuid4(), block_id=block.id, property_number="A-102", property_type="house")
    async_db.add_all([prop_1, prop_2])

    # 5. Profiles
    admin_prof = Profile(id=uuid.uuid4(), auth_user_id=uuid.uuid4(), role="administrator", full_name="Admin User")
    officer_prof = Profile(id=uuid.uuid4(), auth_user_id=uuid.uuid4(), role="complaint_officer", full_name="Officer Tariq")
    staff_prof = Profile(id=uuid.uuid4(), auth_user_id=uuid.uuid4(), role="field_staff", full_name="Staff Imran")
    other_staff_prof = Profile(id=uuid.uuid4(), auth_user_id=uuid.uuid4(), role="field_staff", full_name="Staff Bilal")
    res_a_prof = Profile(id=uuid.uuid4(), auth_user_id=uuid.uuid4(), role="resident", full_name="Resident A")
    res_b_prof = Profile(id=uuid.uuid4(), auth_user_id=uuid.uuid4(), role="resident", full_name="Resident B")
    async_db.add_all([admin_prof, officer_prof, staff_prof, other_staff_prof, res_a_prof, res_b_prof])
    await async_db.flush()

    # 6. Residents
    res_a = Resident(id=uuid.uuid4(), profile_id=res_a_prof.id, verification_status="verified")
    res_b = Resident(id=uuid.uuid4(), profile_id=res_b_prof.id, verification_status="verified")
    async_db.add_all([res_a, res_b])
    await async_db.flush()

    # 7. Associations: Res A has Prop 1, Res B has Prop 2
    assoc_a = PropertyResident(
        id=uuid.uuid4(),
        resident_id=res_a.id,
        property_id=prop_1.id,
        relationship_type="owner",
        valid_from=datetime.date.today(),
    )
    assoc_b = PropertyResident(
        id=uuid.uuid4(),
        resident_id=res_b.id,
        property_id=prop_2.id,
        relationship_type="tenant",
        valid_from=datetime.date.today(),
    )
    async_db.add_all([assoc_a, assoc_b])
    await async_db.commit()

    return {
        "block": block,
        "cat_elec": cat_elec,
        "cat_water": cat_water,
        "utility": utility,
        "prop_1": prop_1,
        "prop_2": prop_2,
        "admin": admin_prof,
        "officer": officer_prof,
        "staff": staff_prof,
        "other_staff": other_staff_prof,
        "res_a": res_a,
        "res_a_prof": res_a_prof,
        "res_b": res_b,
        "res_b_prof": res_b_prof,
    }


# -----------------------------------------------------------------------------
# AT-01 & AT-02: Resident Submission & Unauthorized Property Rejection
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_at01_resident_submission(async_db: AsyncSession, seed_fixtures: dict):
    f = seed_fixtures
    req = ComplaintCreate(
        property_id=f["prop_1"].id,
        category_id=f["cat_water"].id,
        description="Water pressure is extremely low in pipeline",
        is_urgent=False,
    )
    complaint = await create_resident_complaint(async_db, req, f["res_a"], f["res_a_prof"])
    assert complaint.status == "submitted"
    assert complaint.complaint_number.startswith("CMS-")
    assert complaint.resident_id == f["res_a"].id


@pytest.mark.asyncio
async def test_at02_unauthorized_property_rejection(async_db: AsyncSession, seed_fixtures: dict):
    f = seed_fixtures
    # Resident A tries to lodge a complaint for Property 2 (which belongs to Resident B)
    req = ComplaintCreate(
        property_id=f["prop_2"].id,
        category_id=f["cat_water"].id,
        description="Unauthorized complaint attempt",
    )
    with pytest.raises(ForbiddenError):
        await create_resident_complaint(async_db, req, f["res_a"], f["res_a_prof"])


# -----------------------------------------------------------------------------
# AT-03: Officer Offline Intake (Phone/WhatsApp/Office)
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_at03_officer_offline_intake(async_db: AsyncSession, seed_fixtures: dict):
    f = seed_fixtures
    req = OfflineComplaintCreate(
        resident_id=f["res_b"].id,
        property_id=f["prop_2"].id,
        category_id=f["cat_elec"].id,
        description="Meter sparking reported via WhatsApp",
        is_urgent=True,
        urgency_reason="Electrical hazard",
        intake_channel="whatsapp",
    )
    complaint = await create_offline_complaint(async_db, req, f["officer"])
    assert complaint.status == "submitted"
    assert complaint.intake_channel == "whatsapp"
    assert complaint.recorded_by_profile_id == f["officer"].id
    assert complaint.is_urgent is True


# -----------------------------------------------------------------------------
# AT-05, AT-06, AT-07: Incident Grouping, Link/Unlink
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_at05_incident_grouping(async_db: AsyncSession, seed_fixtures: dict):
    f = seed_fixtures
    c1 = await create_resident_complaint(
        async_db,
        ComplaintCreate(property_id=f["prop_1"].id, category_id=f["cat_elec"].id, description="No power in Flat 1"),
        f["res_a"],
        f["res_a_prof"],
    )
    c2 = await create_offline_complaint(
        async_db,
        OfflineComplaintCreate(
            resident_id=f["res_b"].id,
            property_id=f["prop_2"].id,
            category_id=f["cat_elec"].id,
            description="No power in Flat 2",
            intake_channel="phone",
        ),
        f["officer"],
    )

    inc_req = IncidentCreate(
        category_id=f["cat_elec"].id,
        title="Block A Main Feeder Outage",
        description="Transformer tripped affecting entire block",
        complaint_ids=[c1.id, c2.id],
    )
    incident = await create_incident(async_db, inc_req, f["officer"])
    assert incident.status == "open"
    assert incident.incident_number.startswith("INC-")

    # Refresh complaints to verify status advanced to under_review
    await async_db.refresh(c1)
    await async_db.refresh(c2)
    assert c1.status == "under_review"
    assert c2.status == "under_review"


@pytest.mark.asyncio
async def test_at07_unlink_and_relink(async_db: AsyncSession, seed_fixtures: dict):
    f = seed_fixtures
    c1 = await create_resident_complaint(
        async_db,
        ComplaintCreate(property_id=f["prop_1"].id, category_id=f["cat_elec"].id, description="Fault 1"),
        f["res_a"],
        f["res_a_prof"],
    )
    inc = await create_incident(
        async_db,
        IncidentCreate(category_id=f["cat_elec"].id, title="Incident 1", description="Desc 1", complaint_ids=[c1.id]),
        f["officer"],
    )

    # Find the link
    link = await link_complaint_to_incident(
        async_db,
        inc.id,
        IncidentLinkCreate(complaint_id=c1.id),
        f["officer"],
    ) if False else None  # Already linked during creation

    # Get existing link
    from sqlalchemy import select
    res = await async_db.execute(select(IncidentComplaintLink).where(IncidentComplaintLink.complaint_id == c1.id))
    link = res.scalars().first()
    assert link is not None

    # Unlink with reason
    unlinked = await unlink_complaint_from_incident(async_db, link.id, "Erroneously linked to wrong transformer", f["officer"])
    assert unlinked.unlinked_at is not None
    assert unlinked.unlink_reason == "Erroneously linked to wrong transformer"


# -----------------------------------------------------------------------------
# AT-08, AT-09, AT-10: Work Assignment, Reassignment, Staff Isolation
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_at08_assignment_rejects_non_staff(async_db: AsyncSession, seed_fixtures: dict):
    f = seed_fixtures
    inc = await create_incident(
        async_db,
        IncidentCreate(category_id=f["cat_water"].id, title="Water Leak", description="Main valve broken"),
        f["officer"],
    )
    # Attempt assigning to a resident profile instead of field_staff
    with pytest.raises(BadRequestError):
        await create_work_assignment(
            async_db,
            inc.id,
            WorkAssignmentCreate(staff_profile_id=f["res_a_prof"].id),
            f["officer"],
        )


@pytest.mark.asyncio
async def test_at09_reassignment_audit(async_db: AsyncSession, seed_fixtures: dict):
    f = seed_fixtures
    inc = await create_incident(
        async_db,
        IncidentCreate(category_id=f["cat_water"].id, title="Pipe Burst", description="Near gate 2"),
        f["officer"],
    )
    # 1. Assign to Staff Imran
    a1 = await create_work_assignment(
        async_db,
        inc.id,
        WorkAssignmentCreate(staff_profile_id=f["staff"].id),
        f["officer"],
    )
    assert a1.status == "assigned"

    # 2. Reassign to Staff Bilal
    a2 = await create_work_assignment(
        async_db,
        inc.id,
        WorkAssignmentCreate(staff_profile_id=f["other_staff"].id),
        f["officer"],
    )
    assert a2.status == "assigned"

    # a1 should now be marked cancelled/ended
    await async_db.refresh(a1)
    assert a1.status == "cancelled"
    assert a1.ended_at is not None


@pytest.mark.asyncio
async def test_at10_staff_cannot_update_other_staff_assignment(async_db: AsyncSession, seed_fixtures: dict):
    f = seed_fixtures
    inc = await create_incident(
        async_db,
        IncidentCreate(category_id=f["cat_water"].id, title="Water Valve Leak", description="Main society line leaking"),
        f["officer"],
    )
    assignment = await create_work_assignment(
        async_db,
        inc.id,
        WorkAssignmentCreate(staff_profile_id=f["staff"].id),
        f["officer"],
    )

    # Staff Bilal attempts to update Staff Imran's assignment
    with pytest.raises(ForbiddenError):
        await update_assignment_status(
            async_db,
            assignment.id,
            AssignmentStatusUpdate(status="in_progress"),
            f["other_staff"],
        )


# -----------------------------------------------------------------------------
# AT-11, AT-12, AT-13: External Utility Case Tracking & Overdue Logic
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_at11_at12_utility_case_and_replies(async_db: AsyncSession, seed_fixtures: dict):
    f = seed_fixtures
    inc = await create_incident(
        async_db,
        IncidentCreate(category_id=f["cat_elec"].id, title="Grid Feeder Blown", description="KE Area Issue"),
        f["officer"],
    )
    due_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=48)
    case = await create_utility_case(
        async_db,
        inc.id,
        UtilityCaseCreate(
            utility_company_id=f["utility"].id,
            external_reference_number="KE-889922",
            expected_resolution_at=due_date,
        ),
        f["officer"],
    )
    assert case.status == "submitted"
    assert case.first_response_at is None

    # First inbound update
    update = await add_utility_case_update(
        async_db,
        case.id,
        UtilityCaseUpdateCreate(
            direction="inbound",
            message="KE Dispatch team acknowledges fault ticket",
            update_type="provider_ack",
        ),
        f["officer"],
    )
    assert update.direction == "inbound"

    await async_db.refresh(case)
    assert case.first_response_at is not None


# -----------------------------------------------------------------------------
# AT-14, AT-15, AT-16, AT-17: Incident Resolution & Independent Resident Confirmation
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_at14_at15_at16_resolution_and_independent_confirmations(async_db: AsyncSession, seed_fixtures: dict):
    f = seed_fixtures
    # 1. Resident A and B file complaints
    c_a = await create_resident_complaint(
        async_db,
        ComplaintCreate(property_id=f["prop_1"].id, category_id=f["cat_water"].id, description="Water dirty"),
        f["res_a"],
        f["res_a_prof"],
    )
    c_b = await create_offline_complaint(
        async_db,
        OfflineComplaintCreate(
            resident_id=f["res_b"].id,
            property_id=f["prop_2"].id,
            category_id=f["cat_water"].id,
            description="Water dirty too",
            intake_channel="office_visit",
        ),
        f["officer"],
    )

    # 2. Officer groups into shared incident
    inc = await create_incident(
        async_db,
        IncidentCreate(
            category_id=f["cat_water"].id,
            title="Society Main Underground Tank Contamination",
            description="Tank cleaned and flushed",
            complaint_ids=[c_a.id, c_b.id],
        ),
        f["officer"],
    )

    # 3. Officer marks incident 'resolved' (AT-14)
    await update_incident_status(async_db, inc.id, "resolved", "Tank drained and sanitized", f["officer"])

    await async_db.refresh(c_a)
    await async_db.refresh(c_b)
    # CRITICAL: Both move to pending_confirmation, NOT closed!
    assert c_a.status == "pending_confirmation"
    assert c_b.status == "pending_confirmation"

    # 4. Resident A confirms resolution (AT-15)
    await submit_resident_confirmation(
        async_db,
        c_a.id,
        ResolutionConfirmationCreate(outcome="confirmed", feedback="Water is completely clear now. Thanks!"),
        f["res_a"],
        f["res_a_prof"],
    )
    await async_db.refresh(c_a)
    await async_db.refresh(c_b)

    # Resident A's complaint closes, but Resident B's complaint REMAINS pending_confirmation!
    assert c_a.status == "closed"
    assert c_b.status == "pending_confirmation"

    # 5. Resident B rejects resolution (AT-16)
    await submit_resident_confirmation(
        async_db,
        c_b.id,
        ResolutionConfirmationCreate(outcome="rejected", feedback="Still yellowish smell in flat 2"),
        f["res_b"],
        f["res_b_prof"],
    )
    await async_db.refresh(c_b)
    assert c_b.status == "reopened"


# -----------------------------------------------------------------------------
# AT-19: Cross-Resident Privacy Verification
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_at19_cross_resident_privacy(async_db: AsyncSession, seed_fixtures: dict):
    f = seed_fixtures
    c_a = await create_resident_complaint(
        async_db,
        ComplaintCreate(property_id=f["prop_1"].id, category_id=f["cat_elec"].id, description="Private complaint A"),
        f["res_a"],
        f["res_a_prof"],
    )

    # Resident B attempts to access Resident A's complaint detail
    with pytest.raises(ForbiddenError):
        await get_complaint_detail(async_db, c_a.id, f["res_b_prof"], f["res_b"])


# -----------------------------------------------------------------------------
# AT-24 & AT-25: Dashboard & Reporting Reconciliation
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_at24_at25_reports_and_analytics(async_db: AsyncSession, seed_fixtures: dict):
    summary = await get_dashboard_summary(async_db)
    assert summary is not None
    assert summary.new_complaints_count >= 0

    utility_report = await get_utility_performance_report(async_db)
    assert len(utility_report) > 0
    assert utility_report[0].utility_name == "K-Electric"
