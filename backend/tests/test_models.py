import uuid
from datetime import datetime, timezone
from app.database import Base
from app.models.entities import (
    Block,
    Property,
    Profile,
    Complaint,
)


def test_models_metadata_registered():
    """Verify all 20 required tables are registered in SQLAlchemy metadata."""
    expected_tables = {
        "blocks",
        "properties",
        "profiles",
        "residents",
        "property_residents",
        "categories",
        "utility_companies",
        "complaints",
        "incidents",
        "incident_complaint_links",
        "work_assignments",
        "assignment_updates",
        "utility_cases",
        "utility_case_updates",
        "complaint_status_history",
        "incident_status_history",
        "resolution_confirmations",
        "audit_logs",
        "notifications",
        "attachments",
    }
    actual_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(actual_tables), f"Missing tables: {expected_tables - actual_tables}"


def test_complaint_and_incident_constraints():
    """Verify critical constraints on Complaint, Incident and Links."""
    complaints_table = Base.metadata.tables["complaints"]
    assert "complaint_number" in complaints_table.c
    assert "status" in complaints_table.c
    assert "is_urgent" in complaints_table.c

    incidents_table = Base.metadata.tables["incidents"]
    assert "incident_number" in incidents_table.c
    assert "routing_type" in incidents_table.c
    assert "priority" in incidents_table.c

    links_table = Base.metadata.tables["incident_complaint_links"]
    assert "complaint_id" in links_table.c
    assert "incident_id" in links_table.c
    assert "unlinked_at" in links_table.c


def test_instantiate_sample_records():
    """Verify entities can be created in memory with valid fields."""
    block_id = uuid.uuid4()
    block = Block(id=block_id, code="BLK-A", name="Block A")
    assert block.code == "BLK-A"

    prop_id = uuid.uuid4()
    prop = Property(
        id=prop_id,
        block_id=block_id,
        property_number="A-101",
        property_type="house",
    )
    assert prop.property_number == "A-101"

    profile_id = uuid.uuid4()
    profile = Profile(
        id=profile_id,
        auth_user_id=uuid.uuid4(),
        role="resident",
        full_name="Ahmed Khan",
        email="ahmed@example.com",
    )
    assert profile.role == "resident"

    complaint = Complaint(
        id=uuid.uuid4(),
        complaint_number="CMS-2026-000001",
        resident_id=uuid.uuid4(),
        property_id=prop_id,
        category_id=uuid.uuid4(),
        description="Water supply stopped",
        status="submitted",
        is_urgent=False,
        submitted_at=datetime.now(timezone.utc),
    )
    assert complaint.status == "submitted"
    assert complaint.is_urgent is False
