from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
import logging

from app.core.db import get_db
from app.crud.like import like_crud
from app.crud.poll import poll_crud
from app.schemas.like import LikeResponse, LikeStats
from app.schemas.user import UserResponse
from app.utils.response_helper import (
    success_response, error_response, paginated_response, 
    created_response, updated_response, deleted_response, not_found_response
)
from app.utils.exceptions import LikeNotFoundError, ValidationError, ConflictError
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


@router.post("/poll/{poll_id}", response_model=dict)
async def like_poll(
    request: Request,
    poll_id: UUID = Path(..., description="Poll ID"),
    db: Session = Depends(get_db),
    current_user: Optional[UserResponse] = Depends(get_current_user)
):
    """Like a poll."""
    try:
        # Check if poll exists
        poll = poll_crud.get(db=db, poll_id=poll_id)
        if not poll:
            return not_found_response(resource="Poll", identifier=str(poll_id))
        
        # Get liker identifier
        liker_id = current_user.id if current_user else None
        anon_id = None if current_user else get_anonymous_id(request)
        
        # Check if user has already liked this poll
        existing_like = like_crud.get_by_liker(
            db=db, 
            poll_id=poll_id, 
            user_id=liker_id, 
            anon_id=anon_id
        )
        if existing_like:
            return error_response(
                message="You have already liked this poll",
                status_code=409,
                error="already_liked"
            )
        
        # Create like
        like_data = LikeCreate(
            poll_id=poll_id,
            anon_id=anon_id,
            ip_address=request.client.host if request.client else None
        )
        like = like_crud.create(
            db=db,
            like_data=like_data,
            user_id=liker_id
        )
        
        # Update poll likes count
        poll_crud.update_likes_count(db=db, poll_id=poll_id)
        
        like_response = LikeResponse.model_validate(like)
        
        return created_response(
            data=like_response,
            message="Poll liked successfully"
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
        logger.error(f"Error liking poll: {e}")
        return error_response(
            message="Failed to like poll",
            status_code=500,
            error="internal_error"
        )


@router.delete("/poll/{poll_id}", response_model=dict)
async def unlike_poll(
    request: Request,
    poll_id: UUID = Path(..., description="Poll ID"),
    db: Session = Depends(get_db),
    current_user: Optional[UserResponse] = Depends(get_current_user)
):
    """Unlike a poll."""
    try:
        # Check if poll exists
        poll = poll_crud.get(db=db, poll_id=poll_id)
        if not poll:
            return not_found_response(resource="Poll", identifier=str(poll_id))
        
        # Get liker identifier
        liker_id = current_user.id if current_user else None
        anon_id = None if current_user else get_anonymous_id(request)
        
        # Find existing like
        existing_like = like_crud.get_by_liker(
            db=db, 
            poll_id=poll_id, 
            user_id=liker_id, 
            anon_id=anon_id
        )
        if not existing_like:
            return error_response(
                message="You have not liked this poll",
                status_code=404,
                error="not_liked"
            )
        
        # Delete like
        success = like_crud.delete(db=db, like_id=existing_like.id)
        
        if not success:
            return error_response(
                message="Failed to unlike poll",
                status_code=500,
                error="internal_error"
            )
        
        # Update poll likes count
        poll_crud.update_likes_count(db=db, poll_id=poll_id)
        
        return deleted_response(message="Poll unliked successfully")
        
    except Exception as e:
        logger.error(f"Error unliking poll: {e}")
        return error_response(
            message="Failed to unlike poll",
            status_code=500,
            error="internal_error"
        )


@router.get("/poll/{poll_id}", response_model=dict)
async def get_poll_likes(
    poll_id: UUID = Path(..., description="Poll ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get likes for a specific poll."""
    try:
        # Check if poll exists
        poll = poll_crud.get(db=db, poll_id=poll_id)
        if not poll:
            return not_found_response(resource="Poll", identifier=str(poll_id))
        
        likes = like_crud.get_by_poll(
            db=db, 
            poll_id=poll_id, 
            skip=skip, 
            limit=limit
        )
        
        total = like_crud.count_by_poll(db=db, poll_id=poll_id)
        
        like_responses = [LikeResponse.model_validate(like) for like in likes]
        
        return paginated_response(
            data=like_responses,
            page=(skip // limit) + 1,
            per_page=limit,
            total=total,
            message=f"Likes for poll {poll.title} retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting poll likes {poll_id}: {e}")
        return error_response(
            message="Failed to retrieve poll likes",
            status_code=500,
            error="internal_error"
        )


@router.get("/poll/{poll_id}/stats", response_model=dict)
async def get_poll_like_stats(
    poll_id: UUID = Path(..., description="Poll ID"),
    db: Session = Depends(get_db)
):
    """Get like statistics for a specific poll."""
    try:
        # Check if poll exists
        poll = poll_crud.get(db=db, poll_id=poll_id)
        if not poll:
            return not_found_response(resource="Poll", identifier=str(poll_id))
        
        stats = like_crud.get_poll_stats(db=db, poll_id=poll_id)
        
        return success_response(
            data=stats,
            message=f"Like statistics for poll {poll.title} retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting poll like stats {poll_id}: {e}")
        return error_response(
            message="Failed to retrieve poll like statistics",
            status_code=500,
            error="internal_error"
        )


@router.get("/user/{user_id}", response_model=dict)
async def get_user_likes(
    user_id: UUID = Path(..., description="User ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get likes by a specific user."""
    try:
        likes = like_crud.get_by_user(
            db=db, 
            user_id=user_id, 
            skip=skip, 
            limit=limit
        )
        
        total = like_crud.count_by_user(db=db, user_id=user_id)
        
        like_responses = [LikeResponse.model_validate(like) for like in likes]
        
        return paginated_response(
            data=like_responses,
            page=(skip // limit) + 1,
            per_page=limit,
            total=total,
            message=f"Likes by user {user_id} retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting user likes {user_id}: {e}")
        return error_response(
            message="Failed to retrieve user likes",
            status_code=500,
            error="internal_error"
        )


@router.get("/anonymous/{anon_id}", response_model=dict)
async def get_anonymous_likes(
    anon_id: str = Path(..., description="Anonymous ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get likes by an anonymous user."""
    try:
        likes = like_crud.get_by_anonymous(
            db=db, 
            anon_id=anon_id, 
            skip=skip, 
            limit=limit
        )
        
        total = like_crud.count_by_anonymous(db=db, anon_id=anon_id)
        
        like_responses = [LikeResponse.model_validate(like) for like in likes]
        
        return paginated_response(
            data=like_responses,
            page=(skip // limit) + 1,
            per_page=limit,
            total=total,
            message=f"Likes by anonymous user {anon_id} retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting anonymous likes {anon_id}: {e}")
        return error_response(
            message="Failed to retrieve anonymous likes",
            status_code=500,
            error="internal_error"
        )


@router.get("/{like_id}", response_model=dict)
async def get_like(
    like_id: UUID = Path(..., description="Like ID"),
    db: Session = Depends(get_db)
):
    """Get a specific like by ID."""
    try:
        like = like_crud.get(db=db, like_id=like_id)
        
        if not like:
            return not_found_response(resource="Like", identifier=str(like_id))
        
        like_response = LikeResponse.model_validate(like)
        
        return success_response(
            data=like_response,
            message="Like retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting like {like_id}: {e}")
        return error_response(
            message="Failed to retrieve like",
            status_code=500,
            error="internal_error"
        )


@router.delete("/{like_id}", response_model=dict)
async def delete_like(
    like_id: UUID = Path(..., description="Like ID"),
    db: Session = Depends(get_db),
    current_user: Optional[UserResponse] = Depends(get_current_user)
):
    """Delete a like."""
    try:
        # Get like
        like = like_crud.get(db=db, like_id=like_id)
        if not like:
            return not_found_response(resource="Like", identifier=str(like_id))
        
        # Check authorization (only liker can delete their like)
        if current_user:
            if like.user_id != current_user.id:
                return error_response(
                    message="You can only delete your own likes",
                    status_code=403,
                    error="forbidden"
                )
        else:
            # For anonymous users, we'd need to check anon_id
            # This is a simplified check
            return error_response(
                message="Anonymous likes cannot be deleted",
                status_code=403,
                error="forbidden"
            )
        
        success = like_crud.delete(db=db, like_id=like_id)
        
        if not success:
            return not_found_response(resource="Like", identifier=str(like_id))
        
        # Update poll likes count
        poll_crud.update_likes_count(db=db, poll_id=like.poll_id)
        
        return deleted_response(message="Like deleted successfully")
        
    except Exception as e:
        logger.error(f"Error deleting like {like_id}: {e}")
        return error_response(
            message="Failed to delete like",
            status_code=500,
            error="internal_error"
        )


@router.get("/", response_model=dict)
async def get_likes(
    skip: int = Query(0, ge=0, description="Number of likes to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of likes to return"),
    poll_id: Optional[UUID] = Query(None, description="Filter by poll ID"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db)
):
    """Get list of likes with pagination."""
    try:
        likes = like_crud.get_multiple(
            db=db, 
            skip=skip, 
            limit=limit,
            poll_id=poll_id,
            user_id=user_id
        )
        
        total = like_crud.count(db=db, poll_id=poll_id, user_id=user_id)
        
        like_responses = [LikeResponse.model_validate(like) for like in likes]
        
        return paginated_response(
            data=like_responses,
            page=(skip // limit) + 1,
            per_page=limit,
            total=total,
            message="Likes retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting likes: {e}")
        return error_response(
            message="Failed to retrieve likes",
            status_code=500,
            error="internal_error"
        )
