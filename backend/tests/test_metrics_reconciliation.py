import datetime
import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.entities import (
    Block,
    Category,
    Complaint,
    Incident,
    Profile,
    Property,
    Resident,
    UtilityCase,
    UtilityCompany,
)
from app.services.report_service import (
    get_dashboard_summary,
    get_utility_performance_report,
)


@pytest.fixture
async def report_db():
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


@pytest.mark.asyncio
async def test_kpi_dashboard_reconciliation(report_db: AsyncSession):
    """
    AT-24: Dashboard reconciliation.
    Verifies that dashboard counts match underlying raw table counts precisely.
    """
    block = Block(id=uuid.uuid4(), code="BLK-B", name="Block B")
    report_db.add(block)

    cat = Category(id=uuid.uuid4(), name="Water", description="Water supply")
    report_db.add(cat)

    prop = Property(id=uuid.uuid4(), block_id=block.id, property_number="B-101", property_type="flat")
    report_db.add(prop)

    prof = Profile(id=uuid.uuid4(), auth_user_id=uuid.uuid4(), role="resident", full_name="User")
    report_db.add(prof)
    await report_db.flush()

    res = Resident(id=uuid.uuid4(), profile_id=prof.id, verification_status="verified")
    report_db.add(res)
    await report_db.flush()

    now = datetime.datetime.now(datetime.timezone.utc)

    # 2 submitted complaints, 1 pending_confirmation, 1 closed
    c1 = Complaint(
        id=uuid.uuid4(),
        complaint_number="CMS-2026-000101",
        resident_id=res.id,
        property_id=prop.id,
        category_id=cat.id,
        description="Issue 1",
        status="submitted",
        is_urgent=True,
        submitted_at=now,
    )
    c2 = Complaint(
        id=uuid.uuid4(),
        complaint_number="CMS-2026-000102",
        resident_id=res.id,
        property_id=prop.id,
        category_id=cat.id,
        description="Issue 2",
        status="submitted",
        is_urgent=False,
        submitted_at=now,
    )
    c3 = Complaint(
        id=uuid.uuid4(),
        complaint_number="CMS-2026-000103",
        resident_id=res.id,
        property_id=prop.id,
        category_id=cat.id,
        description="Issue 3",
        status="pending_confirmation",
        is_urgent=False,
        submitted_at=now,
    )
    c4 = Complaint(
        id=uuid.uuid4(),
        complaint_number="CMS-2026-000104",
        resident_id=res.id,
        property_id=prop.id,
        category_id=cat.id,
        description="Issue 4",
        status="closed",
        is_urgent=False,
        submitted_at=now,
    )
    report_db.add_all([c1, c2, c3, c4])

    # 1 open incident
    inc = Incident(
        id=uuid.uuid4(),
        incident_number="INC-2026-000001",
        category_id=cat.id,
        title="Main line burst",
        description="Pipe repair",
        status="in_progress",
        routing_type="internal",
        priority="high",
        created_by=prof.id,
        created_at=now,
    )
    report_db.add(inc)

    # 1 overdue utility case, 1 without due date
    util = UtilityCompany(id=uuid.uuid4(), name="Water Board")
    report_db.add(util)
    await report_db.flush()

    past_due = now - datetime.timedelta(hours=5)
    u_case1 = UtilityCase(
        id=uuid.uuid4(),
        incident_id=inc.id,
        utility_company_id=util.id,
        external_reference_number="KWSC-100",
        status="submitted",
        submitted_at=past_due,
        expected_resolution_at=past_due,  # In past -> Overdue!
        created_by=prof.id,
        created_at=past_due,
    )
    u_case2 = UtilityCase(
        id=uuid.uuid4(),
        incident_id=inc.id,
        utility_company_id=util.id,
        external_reference_number="KWSC-200",
        status="submitted",
        submitted_at=now,
        expected_resolution_at=None,  # No due date -> Not overdue!
        created_by=prof.id,
        created_at=now,
    )
    report_db.add_all([u_case1, u_case2])
    await report_db.commit()

    summary = await get_dashboard_summary(report_db)

    # Reconcile counts
    assert summary.new_complaints_count == 2
    assert summary.pending_complaints_count == 3  # c1, c2, c3 (c4 is closed)
    assert summary.open_incidents_count == 1
    assert summary.pending_confirmations_count == 1  # c3
    assert summary.overdue_utility_cases_count == 1  # u_case1 only
    assert summary.urgent_open_items_count == 1  # c1 is urgent and open


@pytest.mark.asyncio
async def test_at25_utility_analytics_null_safety(report_db: AsyncSession):
    """
    AT-25: Missing reply dates must be excluded from averages, sample count accurately shown.
    """
    util = UtilityCompany(id=uuid.uuid4(), name="SSGC")
    report_db.add(util)
    await report_db.commit()

    report = await get_utility_performance_report(report_db)
    ssgc_row = next((r for r in report if r.utility_name == "SSGC"), None)
    assert ssgc_row is not None
    assert ssgc_row.sample_count == 0
    assert ssgc_row.avg_first_response_hours is None
