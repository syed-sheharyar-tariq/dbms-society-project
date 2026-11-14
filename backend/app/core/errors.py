from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status


class AppError(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        field_errors: Optional[List[Dict[str, Any]]] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(status_code=status_code, detail=message, headers=headers)
        self.code = code
        self.message = message
        self.field_errors = field_errors or []


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found", code: str = "NOT_FOUND"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, code=code, message=message)


class ConflictError(AppError):
    def __init__(self, message: str, code: str = "STATE_CONFLICT"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, code=code, message=message)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Access denied", code: str = "FORBIDDEN"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, code=code, message=message)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required", code: str = "UNAUTHORIZED"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=code,
            message=message,
            headers={"WWW-Authenticate": "Bearer"},
        )


class BadRequestError(AppError):
    def __init__(self, message: str, code: str = "BAD_REQUEST", field_errors: Optional[List[Dict[str, Any]]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=code,
            message=message,
            field_errors=field_errors,
        )
