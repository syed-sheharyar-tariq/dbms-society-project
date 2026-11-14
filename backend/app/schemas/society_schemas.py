import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class BlockBase(BaseModel):
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    is_active: bool = True


class BlockCreate(BlockBase):
    pass


class BlockResponse(BlockBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PropertyBase(BaseModel):
    block_id: uuid.UUID
    property_number: str = Field(..., max_length=40)
    property_type: str = Field(default="house")
    address_note: Optional[str] = None
    is_active: bool = True


class PropertyCreate(PropertyBase):
    pass


class PropertyResponse(PropertyBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    block_name: Optional[str] = None
    block_code: Optional[str] = None


class CategoryBase(BaseModel):
    name: str = Field(..., max_length=80)
    description: Optional[str] = None
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
