from fastapi import HTTPException
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class CustomException(Exception):
    """Custom exception class for application-specific errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "custom_error",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(CustomException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="validation_error",
            details={"field": field, **(details or {})}
        )


class NotFoundError(CustomException):
    """Exception for resource not found errors."""
    
    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource} not found"
        if identifier:
            message += f" with identifier: {identifier}"
        
        super().__init__(
            message=message,
            status_code=404,
            error_code="not_found",
            details={"resource": resource, "identifier": identifier}
        )


class AuthenticationError(CustomException):
    """Exception for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="authentication_error"
        )


class AuthorizationError(CustomException):
    """Exception for authorization errors."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="authorization_error"
        )


class ConflictError(CustomException):
    """Exception for conflict errors (e.g., duplicate resources)."""
    
    def __init__(self, message: str, resource: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=409,
            error_code="conflict_error",
            details={"resource": resource}
        )


class RateLimitError(CustomException):
    """Exception for rate limiting errors."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(
            message=message,
            status_code=429,
            error_code="rate_limit_error",
            details={"retry_after": retry_after}
        )


class PollNotFoundError(NotFoundError):
    """Exception for poll not found."""
    
    def __init__(self, poll_id: str):
        super().__init__(resource="Poll", identifier=poll_id)


class OptionNotFoundError(NotFoundError):
    """Exception for poll option not found."""
    
    def __init__(self, option_id: str):
        super().__init__(resource="Poll option", identifier=option_id)


class UserNotFoundError(NotFoundError):
    """Exception for user not found."""
    
    def __init__(self, user_id: str):
        super().__init__(resource="User", identifier=user_id)


class VoteNotFoundError(NotFoundError):
    """Exception for vote not found."""
    
    def __init__(self, vote_id: str):
        super().__init__(resource="Vote", identifier=vote_id)


class LikeNotFoundError(NotFoundError):
    """Exception for like not found."""
    
    def __init__(self, like_id: str):
        super().__init__(resource="Like", identifier=like_id)


class DuplicateVoteError(ConflictError):
    """Exception for duplicate vote attempts."""
    
    def __init__(self, poll_id: str):
        super().__init__(
            message=f"User has already voted on poll {poll_id}",
            resource="Vote"
        )


class PollExpiredError(CustomException):
    """Exception for expired poll voting attempts."""
    
    def __init__(self, poll_id: str):
        super().__init__(
            message=f"Poll {poll_id} has expired and is no longer accepting votes",
            status_code=410,
            error_code="poll_expired",
            details={"poll_id": poll_id}
        )


class InvalidOptionError(ValidationError):
    """Exception for invalid poll option."""
    
    def __init__(self, option_id: str, poll_id: str):
        super().__init__(
            message=f"Option {option_id} is not valid for poll {poll_id}",
            field="option_id",
            details={"option_id": option_id, "poll_id": poll_id}
        )


class WebSocketConnectionError(CustomException):
    """Exception for WebSocket connection errors."""
    
    def __init__(self, message: str = "WebSocket connection failed"):
        super().__init__(
            message=message,
            status_code=1011,
            error_code="websocket_error"
        )


def handle_database_error(error: Exception) -> CustomException:
    """
    Convert database errors to custom exceptions.
    
    Args:
        error: The database error
        
    Returns:
        CustomException: Appropriate custom exception
    """
    error_message = str(error).lower()
    
    if "unique constraint" in error_message or "duplicate key" in error_message:
        return ConflictError("Resource already exists")
    elif "foreign key constraint" in error_message:
        return ValidationError("Invalid reference to related resource")
    elif "not null constraint" in error_message:
        return ValidationError("Required field is missing")
    elif "check constraint" in error_message:
        return ValidationError("Invalid field value")
    else:
        logger.error(f"Unhandled database error: {error}")
        return CustomException(
            message="Database operation failed",
            status_code=500,
            error_code="database_error"
        )


def handle_redis_error(error: Exception) -> CustomException:
    """
    Convert Redis errors to custom exceptions.
    
    Args:
        error: The Redis error
        
    Returns:
        CustomException: Appropriate custom exception
    """
    logger.error(f"Redis error: {error}")
    return CustomException(
        message="Cache operation failed",
        status_code=503,
        error_code="cache_error"
    )
