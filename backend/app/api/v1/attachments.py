import uuid
from typing import Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import BadRequestError, NotFoundError
from app.core.permissions import get_current_profile
from app.database import get_db
from app.models.entities import Attachment, Profile

router = APIRouter(prefix="/attachments", tags=["Attachments & Storage"])
settings = get_settings()


class AttachmentRecordCreate(BaseModel):
    entity_type: str = Field(..., description="complaint, incident, utility_case, assignment")
    entity_id: uuid.UUID
    file_name: str = Field(..., max_length=255)
    storage_path: str = Field(..., max_length=500)
    mime_type: str = Field(..., max_length=100)
    file_size_bytes: int = Field(..., gt=0, le=10 * 1024 * 1024)  # Max 10MB


class AttachmentResponse(BaseModel):
    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    file_name: str
    storage_path: str
    mime_type: str
    file_size_bytes: int
    download_url: Optional[str] = None


@router.post("", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def register_attachment(
    data: AttachmentRecordCreate,
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    # Allowed MIME types
    allowed_mimes = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
    if data.mime_type not in allowed_mimes:
        raise BadRequestError("File type not allowed. Supported formats: JPG, PNG, WEBP, PDF.")

    attachment = Attachment(
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        uploader_profile_id=profile.id,
        file_name=data.file_name,
        storage_path=data.storage_path,
        mime_type=data.mime_type,
        file_size_bytes=data.file_size_bytes,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)

    download_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_STORAGE_BUCKET}/{attachment.storage_path}"

    return AttachmentResponse(
        id=attachment.id,
        entity_type=attachment.entity_type,
        entity_id=attachment.entity_id,
        file_name=attachment.file_name,
        storage_path=attachment.storage_path,
        mime_type=attachment.mime_type,
        file_size_bytes=attachment.file_size_bytes,
        download_url=download_url,
    )


@router.get("/{attachment_id}/url")
async def get_attachment_download_url(
    attachment_id: uuid.UUID,
    profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    att = await db.get(Attachment, attachment_id)
    if not att:
        raise NotFoundError("Attachment not found.")

    download_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_STORAGE_BUCKET}/{att.storage_path}"
    return {"url": download_url, "file_name": att.file_name, "mime_type": att.mime_type}
