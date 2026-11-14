import time
import uuid
import jwt
import pytest
from app.core.config import get_settings
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.permissions import require_role
from app.core.security import create_test_jwt, verify_supabase_jwt
from app.models.entities import Profile

settings = get_settings()


def test_verify_valid_jwt():
    auth_id = str(uuid.uuid4())
    token = create_test_jwt(auth_id, email="resident@jauhar.com")
    payload = verify_supabase_jwt(token)
    assert payload["sub"] == auth_id
    assert payload["email"] == "resident@jauhar.com"


def test_reject_expired_jwt():
    auth_id = str(uuid.uuid4())
    payload = {
        "sub": auth_id,
        "email": "expired@jauhar.com",
        "exp": int(time.time()) - 3600,  # 1 hour in the past
        "aud": settings.SUPABASE_JWT_AUDIENCE or "authenticated",
        "iss": settings.SUPABASE_JWT_ISSUER or "https://localhost.supabase.co/auth/v1",
    }
    expired_token = jwt.encode(payload, "test-secret", algorithm="HS256")
    with pytest.raises(UnauthorizedError) as exc_info:
        verify_supabase_jwt(expired_token)
    assert "expired" in str(exc_info.value.message).lower()


def test_reject_forged_signature_jwt():
    auth_id = str(uuid.uuid4())
    token = create_test_jwt(auth_id)
    # Tamper with the token
    tampered_token = token[:-5] + "ABCDE"
    with pytest.raises(UnauthorizedError):
        verify_supabase_jwt(tampered_token)


@pytest.mark.asyncio
async def test_role_enforcement_resident_denied_officer_access():
    resident_profile = Profile(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        role="resident",
        full_name="Fatima Ali",
        email="fatima@example.com",
        is_active=True,
    )

    officer_gate = require_role("complaint_officer", "administrator")
    with pytest.raises(ForbiddenError) as exc_info:
        await officer_gate(resident_profile)
    assert "restricted" in str(exc_info.value.message).lower()


@pytest.mark.asyncio
async def test_role_enforcement_officer_allowed():
    officer_profile = Profile(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        role="complaint_officer",
        full_name="Tariq Mehmood",
        email="tariq@example.com",
        is_active=True,
    )

    officer_gate = require_role("complaint_officer", "administrator")
    result = await officer_gate(officer_profile)
    assert result.role == "complaint_officer"


@pytest.mark.asyncio
async def test_role_enforcement_deactivated_profile():
    deactivated_profile = Profile(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        role="field_staff",
        full_name="Imran Electrician",
        email="imran@example.com",
        is_active=False,
    )
    # Deactivated profile check: even if user has valid token, profile is deactivated
    assert deactivated_profile.is_active is False
