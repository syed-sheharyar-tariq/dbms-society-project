import uuid
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import AuditLog


async def log_audit_event(
    db: AsyncSession,
    action: str,
    entity_type: str,
    entity_id: Optional[uuid.UUID] = None,
    actor_profile_id: Optional[uuid.UUID] = None,
    request_id: Optional[str] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """Creates an append-only audit trail record."""
    audit = AuditLog(
        actor_profile_id=actor_profile_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        request_id=request_id,
        old_values=old_values,
        new_values=new_values,
    )
    db.add(audit)
    return audit
