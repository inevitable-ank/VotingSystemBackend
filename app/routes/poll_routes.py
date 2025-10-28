from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request
from sqlalchemy.orm import Session
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
from app.utils.exceptions import PollNotFoundError, ValidationError, ConflictError
from app.core.security import generate_anonymous_id

logger = logging.getLogger(__name__)

router = APIRouter()


def get_current_user(request: Request) -> Optional[UserResponse]:
    """Get current user from request (placeholder for auth)."""
    # This would be implemented with proper authentication
    # For now, return None (anonymous user)
    return None


def get_anonymous_id(request: Request) -> str:
    """Get or create anonymous ID for the request."""
    # This would typically be stored in cookies or session
    # For now, generate a new one each time
    return generate_anonymous_id()


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
        polls = poll_crud.get_multiple(
            db=db, 
            skip=skip, 
            limit=limit, 
            include_expired=include_expired
        )
        
        from app.models.poll import Poll
        total = db.query(Poll).count()
        
        poll_responses = [PollResponse.from_orm(poll) for poll in polls]
        
        return paginated_response(
            data=poll_responses,
            page=(skip // limit) + 1,
            per_page=limit,
            total=total,
            message="Polls retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting polls: {e}")
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
        poll_responses = [PollResponse.from_orm(poll) for poll in polls]
        
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
        poll_responses = [PollResponse.from_orm(poll) for poll in polls]
        
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
        poll_responses = [PollResponse.from_orm(poll) for poll in polls]
        
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
        poll_responses = [PollResponse.from_orm(poll) for poll in polls]
        
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
        poll_responses = [PollResponse.from_orm(poll) for poll in polls]
        
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
        stats = poll_crud.get_stats(db)
        
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
        author_id = current_user.id if current_user else None
        
        poll = poll_crud.create(
            db=db,
            poll_data=poll_data,
            author_id=author_id
        )
        
        poll_response = PollDetail.from_orm(poll)
        
        return created_response(
            data=poll_response,
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
        
        poll_response = PollDetail.from_orm(poll)
        
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
        
        poll_response = PollDetail.from_orm(poll)
        
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
        
        poll_response = PollResponse.from_orm(updated_poll)
        
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
