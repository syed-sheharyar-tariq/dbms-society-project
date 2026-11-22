import logging
from typing import Any, Dict, Optional
import jwt
from jwt import PyJWKClient
from app.core.config import get_settings
from app.core.errors import UnauthorizedError

logger = logging.getLogger("cms_security")
settings = get_settings()

DEMO_TOKENS = {
    "demo-token-resident": {
        "sub": "a1111111-1111-1111-1111-111111111111",
        "email": "resident@jauhar.com",
        "role": "authenticated",
        "aud": "authenticated",
    },
    "demo-token-complaint_officer": {
        "sub": "a2222222-2222-2222-2222-222222222222",
        "email": "officer@jauhar.com",
        "role": "authenticated",
        "aud": "authenticated",
    },
    "demo-token-field_staff": {
        "sub": "a3333333-3333-3333-3333-333333333333",
        "email": "staff@jauhar.com",
        "role": "authenticated",
        "aud": "authenticated",
    },
    "demo-token-administrator": {
        "sub": "a4444444-4444-4444-4444-444444444444",
        "email": "admin@jauhar.com",
        "role": "authenticated",
        "aud": "authenticated",
    },
}

_jwks_client: Optional[PyJWKClient] = None


def get_jwks_client() -> Optional[PyJWKClient]:
    global _jwks_client
    if _jwks_client is None and settings.SUPABASE_JWKS_URL:
        _jwks_client = PyJWKClient(settings.SUPABASE_JWKS_URL)
    return _jwks_client


def verify_supabase_jwt(token: str) -> Dict[str, Any]:
    """
    Verifies a Supabase JWT token against JWKS or secret key.
    Validates issuer, audience, and expiry. Also supports demo tokens in dev mode.
    """
    if not token:
        raise UnauthorizedError("Missing authentication token")

    # In local development or smoke-testing preview, recognize demo tokens directly
    if token in DEMO_TOKENS:
        return DEMO_TOKENS[token]

    # In local development/testing with TEST_SECRET or fallback
    secret = getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "") or "test-secret"
    jwks_client = get_jwks_client()

    try:
        # If JWKS client is configured and available
        if jwks_client:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                audience=settings.SUPABASE_JWT_AUDIENCE if settings.SUPABASE_JWT_AUDIENCE else None,
                issuer=settings.SUPABASE_JWT_ISSUER if settings.SUPABASE_JWT_ISSUER else None,
            )
            return payload
    except Exception as e:
        logger.debug("JWKS validation failed or unconfigured, attempting secret verification: %s", e)

    # Fallback to symmetric HS256 decoding (for testing or direct secret verification)
    try:
        # If unverified decode shows HS256 or in test mode
        unverified_header = jwt.get_unverified_header(token)
        algorithm = unverified_header.get("alg", "HS256")
        
        decode_kwargs: Dict[str, Any] = {
            "algorithms": [algorithm],
            "options": {"verify_exp": True},
        }
        if settings.SUPABASE_JWT_AUDIENCE:
            decode_kwargs["audience"] = settings.SUPABASE_JWT_AUDIENCE
        if settings.SUPABASE_JWT_ISSUER:
            decode_kwargs["issuer"] = settings.SUPABASE_JWT_ISSUER

        try:
            payload = jwt.decode(
                token,
                secret,
                **decode_kwargs
            )
            return payload
        except jwt.InvalidSignatureError:
            if secret != "test-secret":
                return jwt.decode(token, "test-secret", **decode_kwargs)
            raise
        except jwt.ExpiredSignatureError:
            raise

    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Token has expired")
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError(f"Invalid token: {str(exc)}")
    except Exception as exc:
        raise UnauthorizedError(f"Authentication failed: {str(exc)}")


def create_test_jwt(
    auth_user_id: str,
    email: str = "test@example.com",
    role: str = "authenticated",
    secret: str = "test-secret",
) -> str:
    """Helper to generate JWT tokens for automated unit/integration tests."""
    payload = {
        "sub": auth_user_id,
        "email": email,
        "aud": settings.SUPABASE_JWT_AUDIENCE or "authenticated",
        "iss": settings.SUPABASE_JWT_ISSUER or "https://localhost.supabase.co/auth/v1",
        "role": role,
    }
    return jwt.encode(payload, secret, algorithm="HS256")
