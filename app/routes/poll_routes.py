from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
from uuid import UUID
import logging

from app.core.db import get_db
from app.crud.poll import poll_crud
from app.crud.user import user_crud
from app.schemas.poll import PollCreate, PollUpdate, PollResponse, PollDetail, PollList, PollStats, PollSearch
from app.schemas.user import UserResponse
from app.utils.response_helper import (
    success_response, error_response, paginated_response, 
    created_response, updated_response, deleted_response, not_found_response
)
from fastapi.encoders import jsonable_encoder
import json
import asyncio
from app.core.redis_client import get_cache, set_cache
from app.utils.exceptions import PollNotFoundError, ValidationError, ConflictError
from app.core.security import generate_anonymous_id, verify_token
from app.utils.response_helper import unauthorized_response

logger = logging.getLogger(__name__)

router = APIRouter()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[UserResponse]:
    """Extract current user from Authorization Bearer token."""
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return None

    token = auth_header.split(" ", 1)[1].strip()
    payload = verify_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = user_crud.get(db, user_id)
    if not user or not getattr(user, "is_active", True):
        return None

    try:
        return UserResponse.model_validate(user)
    except Exception:
        # Fallback minimal mapping if validation fails
        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            is_verified=getattr(user, "is_verified", False),
            created_at=str(user.created_at),
            updated_at=str(user.updated_at),
            last_login=str(user.last_login) if getattr(user, "last_login", None) else None,
        )


def get_anonymous_id(request: Request) -> str:
    """Get or create anonymous ID for the request."""
    # This would typically be stored in cookies or session
    # For now, generate a new one each time
    return generate_anonymous_id()


@router.get("/db-health", response_model=dict)
async def health_check(db: Session = Depends(get_db)):
    """Database health check endpoint."""
    try:
        # Test basic database connection
        result = db.execute(text("SELECT 1 as health_check"))
        health_status = result.fetchone()[0] == 1
        
        # Test a simple poll query
        from app.models.poll import Poll
        poll_count = db.query(Poll).count()
        
        return success_response(
            data={
                "database": "connected" if health_status else "disconnected",
                "poll_count": poll_count,
                "status": "healthy" if health_status else "unhealthy"
            },
            message="Health check completed"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return error_response(
            message="Health check failed",
            status_code=503,
            error="service_unavailable",
            details=str(e)
        )


@router.get("/", response_model=dict)
async def get_polls(
    skip: int = Query(0, ge=0, description="Number of polls to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of polls to return"),
    category: Optional[str] = Query(None, description="Poll category filter"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    include_expired: bool = Query(False, description="Include expired polls"),
    db: Session = Depends(get_db)
):
    """Get list of polls with pagination."""
    try:
        # Test database connection first
        db.execute(text("SELECT 1"))
        
        polls = poll_crud.get_multiple(
            db=db, 
            skip=skip, 
            limit=limit, 
            include_expired=include_expired
        )
        
        from app.models.poll import Poll
        total = db.query(Poll).count()
        
        poll_responses = [poll.to_dict() for poll in polls]
        
        return paginated_response(
            data=poll_responses,
            page=(skip // limit) + 1,
            per_page=limit,
            total=total,
            message="Polls retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting polls: {e}")
        # Check if it's a connection error
        if "server closed the connection" in str(e) or "connection" in str(e).lower():
            return error_response(
                message="Database connection error. Please try again.",
                status_code=503,
                error="service_unavailable"
            )
        return error_response(
            message="Failed to retrieve polls",
            status_code=500,
            error="internal_error"
        )


@router.get("/public", response_model=dict)
async def get_public_polls(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get public polls."""
    try:
        polls = poll_crud.get_public(db=db, skip=skip, limit=limit)
        poll_responses = [poll.to_dict() for poll in polls]
        
        return success_response(
            data=poll_responses,
            message="Public polls retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting public polls: {e}")
        return error_response(
            message="Failed to retrieve public polls",
            status_code=500
        )


@router.get("/trending", response_model=dict)
async def get_trending_polls(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get trending polls."""
    try:
        polls = poll_crud.get_trending(db=db, skip=skip, limit=limit)
        poll_responses = [poll.to_dict() for poll in polls]
        
        return success_response(
            data=poll_responses,
            message="Trending polls retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting trending polls: {e}")
        return error_response(
            message="Failed to retrieve trending polls",
            status_code=500
        )


@router.get("/popular", response_model=dict)
async def get_popular_polls(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get popular polls."""
    try:
        polls = poll_crud.get_popular(db=db, skip=skip, limit=limit)
        poll_responses = [poll.to_dict() for poll in polls]
        
        return success_response(
            data=poll_responses,
            message="Popular polls retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting popular polls: {e}")
        return error_response(
            message="Failed to retrieve popular polls",
            status_code=500
        )


@router.get("/recent", response_model=dict)
async def get_recent_polls(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get recent polls."""
    try:
        polls = poll_crud.get_recent(db=db, skip=skip, limit=limit)
        poll_responses = [poll.to_dict() for poll in polls]
        
        return success_response(
            data=poll_responses,
            message="Recent polls retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting recent polls: {e}")
        return error_response(
            message="Failed to retrieve recent polls",
            status_code=500
        )


@router.get("/search", response_model=dict)
async def search_polls(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search polls by title or description."""
    try:
        polls = poll_crud.search(db=db, query=q, skip=skip, limit=limit)
        poll_responses = [poll.to_dict() for poll in polls]
        
        return success_response(
            data=poll_responses,
            message=f"Search results for '{q}'"
        )
        
    except Exception as e:
        logger.error(f"Error searching polls: {e}")
        return error_response(
            message="Failed to search polls",
            status_code=500
        )


@router.get("/stats", response_model=dict)
async def get_poll_stats(db: Session = Depends(get_db)):
    """Get poll statistics."""
    try:
        # Try cache first
        cache_key = "stats:polls"
        cached = await get_cache(cache_key)
        if cached:
            return success_response(
                data=json.loads(cached),
                message="Poll statistics retrieved successfully"
            )

        stats = poll_crud.get_stats(db)
        # Cache the stats for a short time to improve first paint
        try:
            await set_cache(cache_key, json.dumps(jsonable_encoder(stats)), expire=30)
        except Exception:
            pass
        
        return success_response(
            data=stats,
            message="Poll statistics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting poll stats: {e}")
        return error_response(
            message="Failed to retrieve poll statistics",
            status_code=500
        )


@router.post("/", response_model=dict)
async def create_poll(
    poll_data: PollCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[UserResponse] = Depends(get_current_user)
):
    """Create a new poll."""
    try:
        if not current_user:
            return unauthorized_response(message="Authentication required to create polls")
        
        author_id = current_user.id
        
        poll = poll_crud.create(
            db=db,
            poll_data=poll_data,
            author_id=author_id
        )
        
        # Convert to dict and return directly without Pydantic validation for now
        poll_dict = poll.to_dict()
        
        return created_response(
            data=poll_dict,
            message="Poll created successfully"
        )
        
    except ValidationError as e:
        return error_response(
            message=str(e),
            status_code=422,
            error="validation_error"
        )
    except ConflictError as e:
        return error_response(
            message=str(e),
            status_code=409,
            error="conflict_error"
        )
    except Exception as e:
        logger.error(f"Error creating poll: {e}")
        return error_response(
            message="Failed to create poll",
            status_code=500
        )


@router.get("/{poll_id}", response_model=dict)
async def get_poll(
    request: Request,
    poll_id: UUID = Path(..., description="Poll ID"),
    db: Session = Depends(get_db)
):
    """Get a specific poll by ID."""
    try:
        poll = poll_crud.get_with_details(db=db, poll_id=poll_id)
        
        if not poll:
            return not_found_response(resource="Poll", identifier=str(poll_id))
        
        # Increment view count
        poll_crud.increment_views(db=db, poll_id=poll_id)
        
        poll_response = poll.to_dict()
        
        return success_response(
            data=poll_response,
            message="Poll retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting poll {poll_id}: {e}")
        return error_response(
            message="Failed to retrieve poll",
            status_code=500
        )


@router.get("/slug/{slug}", response_model=dict)
async def get_poll_by_slug(
    request: Request,
    slug: str = Path(..., description="Poll slug"),
    db: Session = Depends(get_db)
):
    """Get a specific poll by slug."""
    try:
        poll = poll_crud.get_by_slug(db=db, slug=slug)
        
        if not poll:
            return not_found_response(resource="Poll", identifier=slug)
        
        # Increment view count
        poll_crud.increment_views(db=db, poll_id=poll.id)
        
        poll_response = poll.to_dict()
        
        return success_response(
            data=poll_response,
            message="Poll retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting poll by slug {slug}: {e}")
        return error_response(
            message="Failed to retrieve poll",
            status_code=500
        )


@router.put("/{poll_id}", response_model=dict)
async def update_poll(
    poll_id: UUID = Path(..., description="Poll ID"),
    poll_data: PollUpdate = None,
    db: Session = Depends(get_db),
    current_user: Optional[UserResponse] = Depends(get_current_user)
):
    """Update a poll."""
    try:
        # Check if poll exists
        poll = poll_crud.get(db=db, poll_id=poll_id)
        if not poll:
            return not_found_response(resource="Poll", identifier=str(poll_id))
        
        # Check authorization (only author can update)
        if current_user and poll.author_id != current_user.id:
            return error_response(
                message="You can only update your own polls",
                status_code=403,
                error="forbidden"
            )
        
        updated_poll = poll_crud.update(
            db=db,
            poll_id=poll_id,
            poll_data=poll_data
        )
        
        if not updated_poll:
            return not_found_response(resource="Poll", identifier=str(poll_id))
        
        poll_response = updated_poll.to_dict()
        
        return updated_response(
            data=poll_response,
            message="Poll updated successfully"
        )
        
    except ValidationError as e:
        return error_response(
            message=str(e),
            status_code=422,
            error="validation_error"
        )
    except Exception as e:
        logger.error(f"Error updating poll {poll_id}: {e}")
        return error_response(
            message="Failed to update poll",
            status_code=500
        )


@router.delete("/{poll_id}", response_model=dict)
async def delete_poll(
    poll_id: UUID = Path(..., description="Poll ID"),
    db: Session = Depends(get_db),
    current_user: Optional[UserResponse] = Depends(get_current_user)
):
    """Delete a poll."""
    try:
        # Check if poll exists
        poll = poll_crud.get(db=db, poll_id=poll_id)
        if not poll:
            return not_found_response(resource="Poll", identifier=str(poll_id))
        
        # Check authorization (only author can delete)
        if current_user and poll.author_id != current_user.id:
            return error_response(
                message="You can only delete your own polls",
                status_code=403,
                error="forbidden"
            )
        
        success = poll_crud.delete(db=db, poll_id=poll_id)
        
        if not success:
            return not_found_response(resource="Poll", identifier=str(poll_id))
        
        return deleted_response(message="Poll deleted successfully")
        
    except Exception as e:
        logger.error(f"Error deleting poll {poll_id}: {e}")
        return error_response(
            message="Failed to delete poll",
            status_code=500
        )


@router.post("/{poll_id}/activate", response_model=dict)
async def activate_poll(
    poll_id: UUID = Path(..., description="Poll ID"),
    db: Session = Depends(get_db),
    current_user: Optional[UserResponse] = Depends(get_current_user)
):
    """Activate a poll."""
    try:
        # Check if poll exists
        poll = poll_crud.get(db=db, poll_id=poll_id)
        if not poll:
            return not_found_response(resource="Poll", identifier=str(poll_id))
        
        # Check authorization
        if current_user and poll.author_id != current_user.id:
            return error_response(
                message="You can only activate your own polls",
                status_code=403,
                error="forbidden"
            )
        
        success = poll_crud.activate(db=db, poll_id=poll_id)
        
        if not success:
            return not_found_response(resource="Poll", identifier=str(poll_id))
        
        return success_response(
            message="Poll activated successfully"
        )
        
    except Exception as e:
        logger.error(f"Error activating poll {poll_id}: {e}")
        return error_response(
            message="Failed to activate poll",
            status_code=500
        )


@router.post("/{poll_id}/deactivate", response_model=dict)
async def deactivate_poll(
    poll_id: UUID = Path(..., description="Poll ID"),
    db: Session = Depends(get_db),
    current_user: Optional[UserResponse] = Depends(get_current_user)
):
    """Deactivate a poll."""
    try:
        # Check if poll exists
        poll = poll_crud.get(db=db, poll_id=poll_id)
        if not poll:
            return not_found_response(resource="Poll", identifier=str(poll_id))
        
        # Check authorization
        if current_user and poll.author_id != current_user.id:
            return error_response(
                message="You can only deactivate your own polls",
                status_code=403,
                error="forbidden"
            )
        
        success = poll_crud.deactivate(db=db, poll_id=poll_id)
        
        if not success:
            return not_found_response(resource="Poll", identifier=str(poll_id))
        
        return success_response(
            message="Poll deactivated successfully"
        )
        
    except Exception as e:
        logger.error(f"Error deactivating poll {poll_id}: {e}")
        return error_response(
            message="Failed to deactivate poll",
            status_code=500
        )
