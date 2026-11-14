import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class UtilityCompanyBase(BaseModel):
    name: str = Field(..., max_length=150)
    contact_info: Optional[str] = None
    contact_phone: Optional[str] = Field(None, max_length=30)
    contact_email: Optional[str] = Field(None, max_length=254)
    is_active: bool = True


class UtilityCompanyCreate(UtilityCompanyBase):
    pass


class UtilityCompanyResponse(UtilityCompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class UtilityCaseCreate(BaseModel):
    utility_company_id: uuid.UUID
    external_reference_number: Optional[str] = Field(None, max_length=100)
    expected_resolution_at: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=2000)


class UtilityCaseUpdateCreate(BaseModel):
    direction: str = Field(..., description="outbound, inbound, internal_note")
    update_type: str = Field(default="status_update", max_length=40)
    message: str = Field(..., min_length=2, max_length=5000)
    provider_event_at: Optional[datetime] = None
    attachment_path: Optional[str] = Field(None, max_length=500)


class UtilityCaseUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    utility_case_id: uuid.UUID
    actor_profile_id: uuid.UUID
    actor_name: Optional[str] = None
    direction: str
    update_type: str
    message: str
    provider_event_at: Optional[datetime] = None
    recorded_at: datetime
    attachment_path: Optional[str] = None


class UtilityCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    incident_number: Optional[str] = None
    utility_company_id: uuid.UUID
    utility_company_name: Optional[str] = None
    external_reference_number: Optional[str] = None
    status: str
    submitted_at: datetime
    expected_resolution_at: Optional[datetime] = None
    first_response_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_overdue: bool = False
    updates: List[UtilityCaseUpdateResponse] = []
