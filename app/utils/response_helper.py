from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel
from app.utils.logger import get_logger

logger = get_logger("response_helper")


class APIResponse(BaseModel):
    """Standard API response model."""
    
    success: bool = True
    message: str = "Success"
    data: Optional[Any] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PaginatedResponse(BaseModel):
    """Paginated response model."""
    
    success: bool = True
    message: str = "Success"
    data: list[Any] = []
    pagination: Dict[str, Any] = {
        "page": 1,
        "per_page": 20,
        "total": 0,
        "pages": 0,
        "has_next": False,
        "has_prev": False
    }


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Create a success response.
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        details: Additional details
        
    Returns:
        JSONResponse: Success response
    """
    response_data = APIResponse(
        success=True,
        message=message,
        data=data,
        details=details
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data.dict()
    )


def error_response(
    message: str = "Error",
    status_code: int = 400,
    error: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Create an error response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        error: Error code
        details: Additional details
        
    Returns:
        JSONResponse: Error response
    """
    response_data = APIResponse(
        success=False,
        message=message,
        error=error,
        details=details
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data.dict()
    )


def paginated_response(
    data: list[Any],
    page: int = 1,
    per_page: int = 20,
    total: int = 0,
    message: str = "Success"
) -> JSONResponse:
    """
    Create a paginated response.
    
    Args:
        data: List of data items
        page: Current page number
        per_page: Items per page
        total: Total number of items
        message: Success message
        
    Returns:
        JSONResponse: Paginated response
    """
    pages = (total + per_page - 1) // per_page if total > 0 else 0
    
    pagination = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1
    }
    
    response_data = PaginatedResponse(
        success=True,
        message=message,
        data=data,
        pagination=pagination
    )
    
    return JSONResponse(
        status_code=200,
        content=response_data.dict()
    )


def created_response(
    data: Any = None,
    message: str = "Resource created successfully"
) -> JSONResponse:
    """
    Create a 201 Created response.
    
    Args:
        data: Created resource data
        message: Success message
        
    Returns:
        JSONResponse: Created response
    """
    return success_response(
        data=data,
        message=message,
        status_code=201
    )


def updated_response(
    data: Any = None,
    message: str = "Resource updated successfully"
) -> JSONResponse:
    """
    Create a 200 OK response for updates.
    
    Args:
        data: Updated resource data
        message: Success message
        
    Returns:
        JSONResponse: Updated response
    """
    return success_response(
        data=data,
        message=message,
        status_code=200
    )


def deleted_response(
    message: str = "Resource deleted successfully"
) -> JSONResponse:
    """
    Create a 200 OK response for deletions.
    
    Args:
        message: Success message
        
    Returns:
        JSONResponse: Deleted response
    """
    return success_response(
        message=message,
        status_code=200
    )


def not_found_response(
    resource: str = "Resource",
    identifier: Optional[str] = None
) -> JSONResponse:
    """
    Create a 404 Not Found response.
    
    Args:
        resource: Resource type
        identifier: Resource identifier
        
    Returns:
        JSONResponse: Not found response
    """
    message = f"{resource} not found"
    if identifier:
        message += f" with identifier: {identifier}"
    
    return error_response(
        message=message,
        status_code=404,
        error="not_found",
        details={"resource": resource, "identifier": identifier}
    )


def validation_error_response(
    message: str = "Validation error",
    field: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Create a 422 Validation Error response.
    
    Args:
        message: Error message
        field: Field that failed validation
        details: Additional details
        
    Returns:
        JSONResponse: Validation error response
    """
    return error_response(
        message=message,
        status_code=422,
        error="validation_error",
        details={"field": field, **(details or {})}
    )


def unauthorized_response(
    message: str = "Authentication required"
) -> JSONResponse:
    """
    Create a 401 Unauthorized response.
    
    Args:
        message: Error message
        
    Returns:
        JSONResponse: Unauthorized response
    """
    return error_response(
        message=message,
        status_code=401,
        error="unauthorized"
    )


def forbidden_response(
    message: str = "Insufficient permissions"
) -> JSONResponse:
    """
    Create a 403 Forbidden response.
    
    Args:
        message: Error message
        
    Returns:
        JSONResponse: Forbidden response
    """
    return error_response(
        message=message,
        status_code=403,
        error="forbidden"
    )


def conflict_response(
    message: str = "Resource conflict",
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Create a 409 Conflict response.
    
    Args:
        message: Error message
        details: Additional details
        
    Returns:
        JSONResponse: Conflict response
    """
    return error_response(
        message=message,
        status_code=409,
        error="conflict",
        details=details
    )


def rate_limit_response(
    message: str = "Rate limit exceeded",
    retry_after: Optional[int] = None
) -> JSONResponse:
    """
    Create a 429 Rate Limit response.
    
    Args:
        message: Error message
        retry_after: Seconds to wait before retrying
        
    Returns:
        JSONResponse: Rate limit response
    """
    return error_response(
        message=message,
        status_code=429,
        error="rate_limit",
        details={"retry_after": retry_after}
    )


def internal_error_response(
    message: str = "Internal server error",
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Create a 500 Internal Server Error response.
    
    Args:
        message: Error message
        details: Additional details
        
    Returns:
        JSONResponse: Internal error response
    """
    logger.error("Internal server error", message=message, details=details)
    
    return error_response(
        message=message,
        status_code=500,
        error="internal_error",
        details=details
    )


def service_unavailable_response(
    message: str = "Service temporarily unavailable"
) -> JSONResponse:
    """
    Create a 503 Service Unavailable response.
    
    Args:
        message: Error message
        
    Returns:
        JSONResponse: Service unavailable response
    """
    return error_response(
        message=message,
        status_code=503,
        error="service_unavailable"
    )

