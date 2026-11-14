import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class WorkAssignmentCreate(BaseModel):
    staff_profile_id: uuid.UUID
    notes: Optional[str] = Field(None, max_length=1000)


class AssignmentStatusUpdate(BaseModel):
    status: str = Field(..., description="accepted, in_progress, blocked, completed, cancelled")
    notes: Optional[str] = Field(None, max_length=2000)
    completion_notes: Optional[str] = Field(None, max_length=2000)


class AssignmentProgressNote(BaseModel):
    message: str = Field(..., min_length=2, max_length=2000)
    update_type: str = Field(default="progress_note")


class AssignmentUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assignment_id: uuid.UUID
    actor_profile_id: uuid.UUID
    actor_name: Optional[str] = None
    update_type: str
    message: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    created_at: datetime


class WorkAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    incident_number: Optional[str] = None
    incident_title: Optional[str] = None
    incident_priority: Optional[str] = None
    area_description: Optional[str] = None
    category_name: Optional[str] = None
    staff_profile_id: uuid.UUID
    staff_name: Optional[str] = None
    assigned_by_profile_id: uuid.UUID
    status: str
    assigned_at: datetime
    accepted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    completion_notes: Optional[str] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    updates: List[AssignmentUpdateResponse] = []
