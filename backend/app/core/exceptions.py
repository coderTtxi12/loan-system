"""Custom exceptions for the application."""
from typing import Any, Dict, List, Optional


class BaseAPIException(Exception):
    """Base exception for all API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        errors: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.errors = errors or []
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BaseAPIException):
    """Raised when validation fails."""

    def __init__(
        self,
        message: str = "Validation error",
        errors: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=422,
            errors=errors,
            details=details,
        )


class NotFoundError(BaseAPIException):
    """Raised when a resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=404,
            details=details,
        )


class CreditNotFoundError(NotFoundError):
    """Raised when a credit application is not found."""

    def __init__(self, credit_id: str):
        super().__init__(
            message=f"Credit application {credit_id} not found",
            details={"credit_id": credit_id},
        )


class CountryNotSupportedError(BaseAPIException):
    """Raised when a country is not supported."""

    def __init__(self, message: str, supported_countries: Optional[List[str]] = None):
        super().__init__(
            message=message,
            status_code=400,
            details={"supported_countries": supported_countries or []},
        )


class UnauthorizedError(BaseAPIException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            status_code=401,
        )


class ForbiddenError(BaseAPIException):
    """Raised when access is forbidden."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            message=message,
            status_code=403,
        )


class ConflictError(BaseAPIException):
    """Raised when there's a conflict with the current state."""

    def __init__(
        self,
        message: str = "Conflict",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=409,
            details=details,
        )


class ExternalServiceError(BaseAPIException):
    """Raised when an external service fails."""

    def __init__(
        self,
        service_name: str,
        message: str = "External service error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"{service_name}: {message}",
            status_code=502,
            details={"service": service_name, **(details or {})},
        )
