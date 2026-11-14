import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class IncidentCreate(BaseModel):
    category_id: uuid.UUID
    title: str = Field(..., min_length=5, max_length=180)
    description: str = Field(..., min_length=5, max_length=5000)
    priority: str = Field(default="normal")
    area_description: Optional[str] = Field(None, max_length=500)
    complaint_ids: List[uuid.UUID] = []


class IncidentStatusUpdate(BaseModel):
    status: str = Field(..., description="open, triaged, assigned, in_progress, awaiting_external, resolved, closed, reopened, cancelled")
    reason: Optional[str] = Field(None, max_length=1000)


class IncidentLinkCreate(BaseModel):
    complaint_id: uuid.UUID
    override_category_mismatch: bool = False
    override_reason: Optional[str] = None


class IncidentUnlinkRequest(BaseModel):
    unlink_reason: str = Field(..., min_length=3, max_length=1000)


class IncidentComplaintLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    complaint_id: uuid.UUID
    complaint_number: Optional[str] = None
    linked_at: datetime
    unlinked_at: Optional[datetime] = None
    unlink_reason: Optional[str] = None


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_number: str
    category_id: uuid.UUID
    category_name: Optional[str] = None
    title: str
    description: str
    status: str
    routing_type: str
    priority: str
    area_description: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    updated_at: datetime

    linked_complaint_count: int = 0
    active_complaints: List[dict] = []
