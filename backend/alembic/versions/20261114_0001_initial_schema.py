"""initial_schema

Revision ID: 20261114_0001
Revises: 
Create Date: 2026-11-14 23:05:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20261114_0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Sequences for complaint and incident numbers
    op.execute("CREATE SEQUENCE IF NOT EXISTS complaint_number_seq START 1;")
    op.execute("CREATE SEQUENCE IF NOT EXISTS incident_number_seq START 1;")

    # 1. Blocks
    op.create_table(
        'blocks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(length=20), nullable=False, unique=True),
        sa.Column('name', sa.String(length=100), nullable=False, unique=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 2. Properties
    op.create_table(
        'properties',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('block_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('blocks.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('property_number', sa.String(length=40), nullable=False),
        sa.Column('property_type', sa.String(length=20), nullable=False, server_default='house'),
        sa.Column('address_note', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('block_id', 'property_number', name='uq_properties_block_number'),
        sa.CheckConstraint("property_type IN ('house', 'flat', 'other')", name='chk_properties_property_type'),
    )

    # 3. Profiles
    op.create_table(
        'profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('auth_user_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('role', sa.String(length=30), nullable=False, server_default='resident'),
        sa.Column('full_name', sa.String(length=150), nullable=False),
        sa.Column('phone', sa.String(length=30), nullable=True),
        sa.Column('email', sa.String(length=254), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('administrator', 'complaint_officer', 'field_staff', 'resident')", name='chk_profiles_role'),
    )

    # 4. Residents
    op.create_table(
        'residents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='RESTRICT'), nullable=False, unique=True),
        sa.Column('verification_status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("verification_status IN ('pending', 'verified', 'rejected')", name='chk_residents_verification_status'),
    )

    # 5. Property Residents
    op.create_table(
        'property_residents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('property_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('properties.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('resident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('residents.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('relationship_type', sa.String(length=30), nullable=False, server_default='tenant'),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('is_primary_contact', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("relationship_type IN ('owner', 'tenant', 'family_member', 'authorized_occupant', 'other')", name='chk_property_residents_relationship_type'),
        sa.CheckConstraint("valid_until IS NULL OR valid_until >= valid_from", name='chk_property_resident_dates'),
    )

    # 6. Categories
    op.create_table(
        'categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=80), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 7. Utility Companies
    op.create_table(
        'utility_companies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=150), nullable=False, unique=True),
        sa.Column('contact_info', sa.Text(), nullable=True),
        sa.Column('contact_phone', sa.String(length=30), nullable=True),
        sa.Column('contact_email', sa.String(length=254), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 8. Complaints
    op.create_table(
        'complaints',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('complaint_number', sa.String(length=30), nullable=False, unique=True),
        sa.Column('resident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('residents.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('property_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('properties.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='submitted'),
        sa.Column('is_urgent', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('urgency_reason', sa.Text(), nullable=True),
        sa.Column('intake_channel', sa.String(length=20), nullable=False, server_default='portal'),
        sa.Column('recorded_by_profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('resolved_reported_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('submitted', 'under_review', 'in_progress', 'pending_confirmation', 'reopened', 'closed', 'cancelled')", name='chk_complaints_status'),
        sa.CheckConstraint("intake_channel IN ('portal', 'phone', 'whatsapp', 'office_visit', 'other')", name='chk_complaints_intake_channel'),
    )
    op.create_index('ix_complaints_status_submitted', 'complaints', ['status', sa.text('submitted_at DESC')])
    op.create_index('ix_complaints_resident_submitted', 'complaints', ['resident_id', sa.text('submitted_at DESC')])
    op.create_index('ix_complaints_property_submitted', 'complaints', ['property_id', sa.text('submitted_at DESC')])

    # 9. Incidents
    op.create_table(
        'incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('incident_number', sa.String(length=30), nullable=False, unique=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('title', sa.String(length=180), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='open'),
        sa.Column('routing_type', sa.String(length=20), nullable=False, server_default='unassigned'),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='normal'),
        sa.Column('area_description', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('open', 'triaged', 'assigned', 'in_progress', 'awaiting_external', 'resolved', 'closed', 'reopened', 'cancelled')", name='chk_incidents_status'),
        sa.CheckConstraint("routing_type IN ('unassigned', 'internal', 'external')", name='chk_incidents_routing_type'),
        sa.CheckConstraint("priority IN ('normal', 'high', 'urgent', 'emergency')", name='chk_incidents_priority'),
    )

    # 10. Incident Complaint Links
    op.create_table(
        'incident_complaint_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('incidents.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('complaint_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('complaints.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('linked_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('linked_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('unlinked_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('unlinked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('unlink_reason', sa.Text(), nullable=True),
    )
    op.create_index(
        'uq_active_incident_link_per_complaint',
        'incident_complaint_links',
        ['complaint_id'],
        unique=True,
        postgresql_where=sa.text('unlinked_at IS NULL')
    )
    op.create_index('ix_incident_links_incident', 'incident_complaint_links', ['incident_id'])

    # 11. Work Assignments
    op.create_table(
        'work_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('incidents.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('staff_profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('assigned_by_profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='assigned'),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completion_notes', sa.Text(), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('assigned', 'accepted', 'in_progress', 'blocked', 'completed', 'cancelled')", name='chk_work_assignments_status'),
    )
    op.create_index('ix_assignments_staff_status', 'work_assignments', ['staff_profile_id', 'status'])

    # 12. Assignment Updates
    op.create_table(
        'assignment_updates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('assignment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('work_assignments.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('actor_profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('update_type', sa.String(length=40), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('old_status', sa.String(length=20), nullable=True),
        sa.Column('new_status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 13. Utility Cases
    op.create_table(
        'utility_cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('incidents.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('utility_company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('utility_companies.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('external_reference_number', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='submitted'),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expected_resolution_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('first_response_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('submitted', 'acknowledged', 'in_progress', 'awaiting_info', 'resolved', 'closed', 'cancelled')", name='chk_utility_cases_status'),
    )
    op.create_index(
        'uq_utility_case_provider_reference',
        'utility_cases',
        ['utility_company_id', 'external_reference_number'],
        unique=True,
        postgresql_where=sa.text('external_reference_number IS NOT NULL')
    )
    op.create_index(
        'ix_utility_cases_due',
        'utility_cases',
        ['expected_resolution_at'],
        postgresql_where=sa.text("status NOT IN ('resolved', 'closed', 'cancelled')")
    )

    # 14. Utility Case Updates
    op.create_table(
        'utility_case_updates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('utility_case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('utility_cases.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('actor_profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('direction', sa.String(length=20), nullable=False),
        sa.Column('update_type', sa.String(length=40), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('provider_event_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('attachment_path', sa.String(length=500), nullable=True),
        sa.CheckConstraint("direction IN ('outbound', 'inbound', 'internal_note')", name='chk_utility_updates_direction'),
    )

    # 15. Complaint Status History
    op.create_table(
        'complaint_status_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('complaint_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('complaints.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('old_status', sa.String(length=30), nullable=True),
        sa.Column('new_status', sa.String(length=30), nullable=False),
        sa.Column('changed_by_profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 16. Incident Status History
    op.create_table(
        'incident_status_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('incidents.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('old_status', sa.String(length=30), nullable=True),
        sa.Column('new_status', sa.String(length=30), nullable=False),
        sa.Column('changed_by_profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 17. Resolution Confirmations
    op.create_table(
        'resolution_confirmations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('complaint_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('complaints.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('resident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('residents.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('cycle_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('outcome', sa.String(length=20), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("cycle_number > 0", name='chk_resolution_cycle_number'),
        sa.CheckConstraint("outcome IN ('confirmed', 'rejected')", name='chk_resolution_outcome'),
        sa.UniqueConstraint('complaint_id', 'cycle_number', name='uq_resolution_confirmations_complaint_cycle'),
    )

    # 18. Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('actor_profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(length=60), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('request_id', sa.String(length=64), nullable=True),
        sa.Column('old_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 19. Notifications
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('recipient_profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=True),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 20. Attachments (Supabase Storage integration)
    op.create_table(
        'attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', sa.String(length=40), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('uploader_profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('storage_path', sa.String(length=500), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("entity_type IN ('complaint', 'incident', 'utility_case', 'assignment')", name='chk_attachments_entity_type'),
    )


def downgrade() -> None:
    op.drop_table('attachments')
    op.drop_table('notifications')
    op.drop_table('audit_logs')
    op.drop_table('resolution_confirmations')
    op.drop_table('incident_status_history')
    op.drop_table('complaint_status_history')
    op.drop_table('utility_case_updates')
    op.drop_table('utility_cases')
    op.drop_table('assignment_updates')
    op.drop_table('work_assignments')
    op.drop_table('incident_complaint_links')
    op.drop_table('incidents')
    op.drop_table('complaints')
    op.drop_table('utility_companies')
    op.drop_table('categories')
    op.drop_table('property_residents')
    op.drop_table('residents')
    op.drop_table('profiles')
    op.drop_table('properties')
    op.drop_table('blocks')
    op.execute("DROP SEQUENCE IF EXISTS complaint_number_seq;")
    op.execute("DROP SEQUENCE IF EXISTS incident_number_seq;")
