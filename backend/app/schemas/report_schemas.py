import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class DashboardSummaryResponse(BaseModel):
    new_complaints_count: int = 0
    pending_complaints_count: int = 0
    open_incidents_count: int = 0
    pending_confirmations_count: int = 0
    overdue_utility_cases_count: int = 0
    urgent_open_items_count: int = 0


class RecurringFaultItem(BaseModel):
    block_name: str
    category_name: str
    area_description: Optional[str] = None
    incident_count: int


class StaffWorkloadItem(BaseModel):
    staff_profile_id: uuid.UUID
    staff_name: str
    assigned_count: int
    in_progress_count: int
    blocked_count: int
    total_active: int


class UtilityPerformanceItem(BaseModel):
    utility_company_id: uuid.UUID
    utility_name: str
    total_cases: int
    avg_first_response_hours: Optional[float] = None
    avg_resolution_hours: Optional[float] = None
    sample_count: int = 0


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_profile_id: Optional[uuid.UUID] = None
    actor_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[uuid.UUID] = None
    request_id: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    created_at: datetime
