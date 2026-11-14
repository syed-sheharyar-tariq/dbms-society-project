import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ComplaintCreate(BaseModel):
    property_id: uuid.UUID
    category_id: uuid.UUID
    description: str = Field(..., min_length=5, max_length=5000)
    is_urgent: bool = False
    urgency_reason: Optional[str] = Field(None, max_length=1000)
    intake_channel: str = Field(default="portal")

    @field_validator("description")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Complaint description cannot be empty or blank")
        return trimmed


class OfflineComplaintCreate(ComplaintCreate):
    resident_id: uuid.UUID
    intake_channel: str = Field(..., description="phone, whatsapp, office_visit, other")


class ComplaintStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    old_status: Optional[str] = None
    new_status: str
    reason: Optional[str] = None
    changed_at: datetime
    changed_by_name: Optional[str] = None


class ResolutionConfirmationCreate(BaseModel):
    outcome: str = Field(..., description="confirmed or rejected")
    feedback: Optional[str] = Field(None, max_length=2000)

    @field_validator("outcome")
    @classmethod
    def validate_outcome(cls, v: str) -> str:
        if v not in ("confirmed", "rejected"):
            raise ValueError("Outcome must be either 'confirmed' or 'rejected'")
        return v


class ResolutionConfirmationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    complaint_id: uuid.UUID
    cycle_number: int
    outcome: str
    feedback: Optional[str] = None
    responded_at: datetime


class ComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    complaint_number: str
    resident_id: uuid.UUID
    resident_name: Optional[str] = None
    property_id: uuid.UUID
    property_number: Optional[str] = None
    block_name: Optional[str] = None
    category_id: uuid.UUID
    category_name: Optional[str] = None
    description: str
    status: str
    is_urgent: bool
    urgency_reason: Optional[str] = None
    intake_channel: str
    submitted_at: datetime
    resolved_reported_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    updated_at: datetime

    # Active incident link context
    active_incident_id: Optional[uuid.UUID] = None
    active_incident_number: Optional[str] = None
    status_history: List[ComplaintStatusHistoryResponse] = []
    confirmations: List[ResolutionConfirmationResponse] = []
