import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Uuid as UUID,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Block(Base):
    __tablename__ = "blocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), nullable=False, unique=True)
    name = Column(String(100), nullable=False, unique=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    properties = relationship("Property", back_populates="block", cascade="all, delete-orphan")


class Property(Base):
    __tablename__ = "properties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    block_id = Column(UUID(as_uuid=True), ForeignKey("blocks.id", ondelete="RESTRICT"), nullable=False)
    property_number = Column(String(40), nullable=False)
    property_type = Column(String(20), nullable=False, default="house")
    address_note = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        UniqueConstraint("block_id", "property_number", name="uq_properties_block_number"),
        CheckConstraint("property_type IN ('house', 'flat', 'other')", name="chk_properties_property_type"),
    )

    block = relationship("Block", back_populates="properties")
    property_residents = relationship("PropertyResident", back_populates="property")
    complaints = relationship("Complaint", back_populates="property")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auth_user_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    role = Column(String(30), nullable=False, default="resident")
    full_name = Column(String(150), nullable=False)
    phone = Column(String(30), nullable=True)
    email = Column(String(254), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        CheckConstraint(
            "role IN ('administrator', 'complaint_officer', 'field_staff', 'resident')",
            name="chk_profiles_role",
        ),
    )

    resident = relationship("Resident", back_populates="profile", uselist=False, foreign_keys="Resident.profile_id")
    work_assignments = relationship("WorkAssignment", foreign_keys="WorkAssignment.staff_profile_id", back_populates="staff_profile")


class Resident(Base):
    __tablename__ = "residents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False, unique=True)
    verification_status = Column(String(20), nullable=False, default="pending")
    verified_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        CheckConstraint(
            "verification_status IN ('pending', 'verified', 'rejected')",
            name="chk_residents_verification_status",
        ),
    )

    profile = relationship("Profile", foreign_keys=[profile_id], back_populates="resident")
    verifier = relationship("Profile", foreign_keys=[verified_by])
    property_associations = relationship("PropertyResident", back_populates="resident")
    complaints = relationship("Complaint", back_populates="resident")


class PropertyResident(Base):
    __tablename__ = "property_residents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id", ondelete="RESTRICT"), nullable=False)
    resident_id = Column(UUID(as_uuid=True), ForeignKey("residents.id", ondelete="RESTRICT"), nullable=False)
    relationship_type = Column(String(30), nullable=False, default="tenant")
    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=True)
    is_primary_contact = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        CheckConstraint(
            "relationship_type IN ('owner', 'tenant', 'family_member', 'authorized_occupant', 'other')",
            name="chk_property_residents_relationship_type",
        ),
        CheckConstraint("valid_until IS NULL OR valid_until >= valid_from", name="chk_property_resident_dates"),
    )

    property = relationship("Property", back_populates="property_residents")
    resident = relationship("Resident", back_populates="property_associations")


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(80), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    complaints = relationship("Complaint", back_populates="category")
    incidents = relationship("Incident", back_populates="category")


class UtilityCompany(Base):
    __tablename__ = "utility_companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False, unique=True)
    contact_info = Column(Text, nullable=True)
    contact_phone = Column(String(30), nullable=True)
    contact_email = Column(String(254), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    utility_cases = relationship("UtilityCase", back_populates="utility_company")


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_number = Column(String(30), nullable=False, unique=True)
    resident_id = Column(UUID(as_uuid=True), ForeignKey("residents.id", ondelete="RESTRICT"), nullable=False)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id", ondelete="RESTRICT"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="submitted")
    is_urgent = Column(Boolean, nullable=False, default=False)
    urgency_reason = Column(Text, nullable=True)
    intake_channel = Column(String(20), nullable=False, default="portal")
    recorded_by_profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    resolved_reported_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        CheckConstraint(
            "status IN ('submitted', 'under_review', 'in_progress', 'pending_confirmation', 'reopened', 'closed', 'cancelled')",
            name="chk_complaints_status",
        ),
        CheckConstraint(
            "intake_channel IN ('portal', 'phone', 'whatsapp', 'office_visit', 'other')",
            name="chk_complaints_intake_channel",
        ),
        Index("ix_complaints_status_submitted", "status", text("submitted_at DESC")),
        Index("ix_complaints_resident_submitted", "resident_id", text("submitted_at DESC")),
        Index("ix_complaints_property_submitted", "property_id", text("submitted_at DESC")),
    )

    resident = relationship("Resident", back_populates="complaints")
    property = relationship("Property", back_populates="complaints")
    category = relationship("Category", back_populates="complaints")
    recorder = relationship("Profile", foreign_keys=[recorded_by_profile_id])
    status_history = relationship("ComplaintStatusHistory", back_populates="complaint", cascade="all, delete-orphan")
    incident_links = relationship("IncidentComplaintLink", back_populates="complaint")
    confirmations = relationship("ResolutionConfirmation", back_populates="complaint")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_number = Column(String(30), nullable=False, unique=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    title = Column(String(180), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="open")
    routing_type = Column(String(20), nullable=False, default="unassigned")
    priority = Column(String(20), nullable=False, default="normal")
    area_description = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'triaged', 'assigned', 'in_progress', 'awaiting_external', 'resolved', 'closed', 'reopened', 'cancelled')",
            name="chk_incidents_status",
        ),
        CheckConstraint(
            "routing_type IN ('unassigned', 'internal', 'external')",
            name="chk_incidents_routing_type",
        ),
        CheckConstraint(
            "priority IN ('normal', 'high', 'urgent', 'emergency')",
            name="chk_incidents_priority",
        ),
    )

    category = relationship("Category", back_populates="incidents")
    creator = relationship("Profile", foreign_keys=[created_by])
    complaint_links = relationship("IncidentComplaintLink", back_populates="incident")
    assignments = relationship("WorkAssignment", back_populates="incident")
    utility_cases = relationship("UtilityCase", back_populates="incident")
    status_history = relationship("IncidentStatusHistory", back_populates="incident", cascade="all, delete-orphan")


class IncidentComplaintLink(Base):
    __tablename__ = "incident_complaint_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="RESTRICT"), nullable=False)
    complaint_id = Column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="RESTRICT"), nullable=False)
    linked_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False)
    linked_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    unlinked_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    unlinked_at = Column(DateTime(timezone=True), nullable=True)
    unlink_reason = Column(Text, nullable=True)

    __table_args__ = (
        Index(
            "uq_active_incident_link_per_complaint",
            "complaint_id",
            unique=True,
            postgresql_where=text("unlinked_at IS NULL"),
        ),
        Index("ix_incident_links_incident", "incident_id"),
    )

    incident = relationship("Incident", back_populates="complaint_links")
    complaint = relationship("Complaint", back_populates="incident_links")
    linker = relationship("Profile", foreign_keys=[linked_by])
    unlinker = relationship("Profile", foreign_keys=[unlinked_by])


class WorkAssignment(Base):
    __tablename__ = "work_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="RESTRICT"), nullable=False)
    staff_profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False)
    assigned_by_profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False)
    status = Column(String(20), nullable=False, default="assigned")
    assigned_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completion_notes = Column(Text, nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        CheckConstraint(
            "status IN ('assigned', 'accepted', 'in_progress', 'blocked', 'completed', 'cancelled')",
            name="chk_work_assignments_status",
        ),
        Index("ix_assignments_staff_status", "staff_profile_id", "status"),
    )

    incident = relationship("Incident", back_populates="assignments")
    staff_profile = relationship("Profile", foreign_keys=[staff_profile_id], back_populates="work_assignments")
    assigner_profile = relationship("Profile", foreign_keys=[assigned_by_profile_id])
    updates = relationship("AssignmentUpdate", back_populates="assignment", cascade="all, delete-orphan")


class AssignmentUpdate(Base):
    __tablename__ = "assignment_updates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("work_assignments.id", ondelete="RESTRICT"), nullable=False)
    actor_profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False)
    update_type = Column(String(40), nullable=False)
    message = Column(Text, nullable=False)
    old_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    assignment = relationship("WorkAssignment", back_populates="updates")
    actor = relationship("Profile", foreign_keys=[actor_profile_id])


class UtilityCase(Base):
    __tablename__ = "utility_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="RESTRICT"), nullable=False)
    utility_company_id = Column(UUID(as_uuid=True), ForeignKey("utility_companies.id", ondelete="RESTRICT"), nullable=False)
    external_reference_number = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="submitted")
    submitted_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    expected_resolution_at = Column(DateTime(timezone=True), nullable=True)
    first_response_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        CheckConstraint(
            "status IN ('submitted', 'acknowledged', 'in_progress', 'awaiting_info', 'resolved', 'closed', 'cancelled')",
            name="chk_utility_cases_status",
        ),
        Index(
            "uq_utility_case_provider_reference",
            "utility_company_id",
            "external_reference_number",
            unique=True,
            postgresql_where=text("external_reference_number IS NOT NULL"),
        ),
        Index(
            "ix_utility_cases_due",
            "expected_resolution_at",
            postgresql_where=text("status NOT IN ('resolved', 'closed', 'cancelled')"),
        ),
    )

    incident = relationship("Incident", back_populates="utility_cases")
    utility_company = relationship("UtilityCompany", back_populates="utility_cases")
    creator = relationship("Profile", foreign_keys=[created_by])
    updates = relationship("UtilityCaseUpdate", back_populates="utility_case", cascade="all, delete-orphan")


class UtilityCaseUpdate(Base):
    __tablename__ = "utility_case_updates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    utility_case_id = Column(UUID(as_uuid=True), ForeignKey("utility_cases.id", ondelete="RESTRICT"), nullable=False)
    actor_profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False)
    direction = Column(String(20), nullable=False)
    update_type = Column(String(40), nullable=False)
    message = Column(Text, nullable=False)
    provider_event_at = Column(DateTime(timezone=True), nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    attachment_path = Column(String(500), nullable=True)

    __table_args__ = (
        CheckConstraint("direction IN ('outbound', 'inbound', 'internal_note')", name="chk_utility_updates_direction"),
    )

    utility_case = relationship("UtilityCase", back_populates="updates")
    actor = relationship("Profile", foreign_keys=[actor_profile_id])


class ComplaintStatusHistory(Base):
    __tablename__ = "complaint_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="RESTRICT"), nullable=False)
    old_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=False)
    changed_by_profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False)
    reason = Column(Text, nullable=True)
    changed_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    complaint = relationship("Complaint", back_populates="status_history")
    changed_by = relationship("Profile", foreign_keys=[changed_by_profile_id])


class IncidentStatusHistory(Base):
    __tablename__ = "incident_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="RESTRICT"), nullable=False)
    old_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=False)
    changed_by_profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False)
    reason = Column(Text, nullable=True)
    changed_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    incident = relationship("Incident", back_populates="status_history")
    changed_by = relationship("Profile", foreign_keys=[changed_by_profile_id])


class ResolutionConfirmation(Base):
    __tablename__ = "resolution_confirmations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="RESTRICT"), nullable=False)
    resident_id = Column(UUID(as_uuid=True), ForeignKey("residents.id", ondelete="RESTRICT"), nullable=False)
    cycle_number = Column(Integer, nullable=False, default=1)
    outcome = Column(String(20), nullable=False)
    feedback = Column(Text, nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        CheckConstraint("cycle_number > 0", name="chk_resolution_cycle_number"),
        CheckConstraint("outcome IN ('confirmed', 'rejected')", name="chk_resolution_outcome"),
        UniqueConstraint("complaint_id", "cycle_number", name="uq_resolution_confirmations_complaint_cycle"),
    )

    complaint = relationship("Complaint", back_populates="confirmations")
    resident = relationship("Resident")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(60), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    request_id = Column(String(64), nullable=True)
    old_values = Column(JSON_TYPE, nullable=True)
    new_values = Column(JSON_TYPE, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    actor = relationship("Profile", foreign_keys=[actor_profile_id])


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient_profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(150), nullable=False)
    body = Column(Text, nullable=False)
    target_type = Column(String(50), nullable=True)
    target_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    read_at = Column(DateTime(timezone=True), nullable=True)

    recipient = relationship("Profile", foreign_keys=[recipient_profile_id])


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(40), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    uploader_profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False)
    file_name = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('complaint', 'incident', 'utility_case', 'assignment')",
            name="chk_attachments_entity_type",
        ),
    )

    uploader = relationship("Profile", foreign_keys=[uploader_profile_id])
