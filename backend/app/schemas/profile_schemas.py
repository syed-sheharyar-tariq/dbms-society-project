import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProfileBase(BaseModel):
    full_name: str = Field(..., max_length=150)
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[EmailStr] = None


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=150)
    phone: Optional[str] = Field(None, max_length=30)


class ProfileResponse(ProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    auth_user_id: uuid.UUID
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PropertyResidentAssociation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    property_id: uuid.UUID
    property_number: str
    block_code: str
    relationship_type: str
    is_primary_contact: bool
    valid_from: date
    valid_until: Optional[date] = None


class ResidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    profile_id: uuid.UUID
    verification_status: str
    verified_at: Optional[datetime] = None
    properties: List[PropertyResidentAssociation] = []


class MeResponse(BaseModel):
    profile: ProfileResponse
    resident: Optional[ResidentResponse] = None


class RegisterProfileRequest(BaseModel):
    auth_user_id: Optional[uuid.UUID] = None
    email: Optional[EmailStr] = None
    full_name: str = Field(..., max_length=150)
    phone: Optional[str] = Field(None, max_length=30)
    role: str = Field(default="resident", description="resident, field_staff, complaint_officer, administrator")
    trade_specialization: Optional[str] = None
    desk_location: Optional[str] = None
    badge_id: Optional[str] = None
    property_id: Optional[uuid.UUID] = None
    block_id: Optional[uuid.UUID] = None
    new_property_number: Optional[str] = None
    relationship_type: Optional[str] = "owner"
    admin_passcode: Optional[str] = None

