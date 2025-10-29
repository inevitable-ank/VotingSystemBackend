from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
import logging

from app.core.db import get_db
from app.crud.vote import vote_crud
from app.crud.poll import poll_crud
from app.schemas.vote import VoteCreate, VoteResponse, VoteStats, MultipleVoteCreate
from app.schemas.user import UserResponse
from app.utils.response_helper import (
    success_response, error_response, paginated_response, 
    created_response, updated_response, deleted_response, not_found_response
)
from app.utils.exceptions import VoteNotFoundError, ValidationError, ConflictError
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

    from app.crud.user import user_crud  # local import to avoid circular
    user = user_crud.get(db, user_id)
    if not user or not getattr(user, "is_active", True):
        return None

    try:
        return UserResponse.model_validate(user)
    except Exception:
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


@router.post("/", response_model=dict)
async def cast_vote(
    vote_data: MultipleVoteCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[UserResponse] = Depends(get_current_user)
):
    """Cast a vote on a poll."""
    try:
        if not current_user:
            return unauthorized_response(message="Authentication required to vote")

        # Get poll to validate
        poll = poll_crud.get_with_options(db=db, poll_id=vote_data.poll_id)
        if not poll:
            return not_found_response(resource="Poll", identifier=str(vote_data.poll_id))
        
        # Check if poll is active and not expired
        if not poll.can_vote:
            return error_response(
                message="Poll is not active or has expired",
                status_code=400,
                error="poll_inactive"
            )
        
        # Check if poll allows multiple votes
        if not poll.allow_multiple and len(vote_data.option_ids) > 1:
            return error_response(
                message="Poll does not allow multiple votes",
                status_code=400,
                error="multiple_votes_not_allowed"
            )
        
        # Validate option IDs belong to the poll
        poll_option_ids = {str(option.id) for option in poll.options}
        for option_id in vote_data.option_ids:
            if str(option_id) not in poll_option_ids:
                return error_response(
                    message=f"Option {option_id} does not belong to this poll",
                    status_code=400,
                    error="invalid_option"
                )
        
        # Voter identifier must be authenticated
        voter_id = current_user.id
        anon_id = None
        
        # Check if user has already voted (for single-choice polls)
        if not poll.allow_multiple:
            existing_vote = vote_crud.get_user_vote(
                db=db, 
                poll_id=vote_data.poll_id, 
                user_id=voter_id, 
                anon_id=anon_id
            )
            if existing_vote:
                return error_response(
                    message="You have already voted on this poll",
                    status_code=409,
                    error="already_voted"
                )
        
        # Create votes
        if not poll.allow_multiple:
            # Treat as single-choice: create one vote with the first option_id
            single_vote = vote_crud.create(
                db=db,
                vote_data=VoteCreate(
                    poll_id=vote_data.poll_id,
                    option_id=vote_data.option_ids[0],
                    anon_id=anon_id,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent")
                ),
                user_id=voter_id
            )
            votes = [single_vote]
        else:
            votes = vote_crud.create_multiple(
                db=db,
                vote_data=MultipleVoteCreate(
                    poll_id=vote_data.poll_id,
                    option_ids=vote_data.option_ids,
                    anon_id=anon_id,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent")
                ),
                user_id=voter_id
            )
        
        # Update poll vote counts
        poll_crud.update_vote_counts(db=db, poll_id=vote_data.poll_id)
        
        vote_responses = [VoteResponse.model_validate(vote) for vote in votes]
        
        return created_response(
            data=vote_responses,
            message="Vote cast successfully"
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
        logger.error(f"Error casting vote: {e}")
        return error_response(
            message="Failed to cast vote",
            status_code=500,
            error="internal_error"
        )


@router.get("/poll/{poll_id}", response_model=dict)
async def get_poll_votes(
    poll_id: UUID = Path(..., description="Poll ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get votes for a specific poll."""
    try:
        # Check if poll exists
        poll = poll_crud.get(db=db, poll_id=poll_id)
        if not poll:
            return not_found_response(resource="Poll", identifier=str(poll_id))
        
        votes = vote_crud.get_by_poll(
            db=db, 
            poll_id=poll_id, 
            skip=skip, 
            limit=limit
        )
        
        total = vote_crud.count_by_poll(db=db, poll_id=poll_id)
        
        vote_responses = [VoteResponse.model_validate(vote) for vote in votes]
        
        return paginated_response(
            data=vote_responses,
            page=(skip // limit) + 1,
            per_page=limit,
            total=total,
            message=f"Votes for poll {poll.title} retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting poll votes {poll_id}: {e}")
        return error_response(
            message="Failed to retrieve poll votes",
            status_code=500,
            error="internal_error"
        )


@router.get("/poll/{poll_id}/stats", response_model=dict)
async def get_poll_vote_stats(
    poll_id: UUID = Path(..., description="Poll ID"),
    db: Session = Depends(get_db)
):
    """Get vote statistics for a specific poll."""
    try:
        # Check if poll exists
        poll = poll_crud.get_with_options(db=db, poll_id=poll_id)
        if not poll:
            return not_found_response(resource="Poll", identifier=str(poll_id))
        
        stats = vote_crud.get_poll_stats(db=db, poll_id=poll_id)
        
        return success_response(
            data=stats,
            message=f"Vote statistics for poll {poll.title} retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting poll vote stats {poll_id}: {e}")
        return error_response(
            message="Failed to retrieve poll vote statistics",
            status_code=500,
            error="internal_error"
        )


@router.get("/user/{user_id}", response_model=dict)
async def get_user_votes(
    user_id: UUID = Path(..., description="User ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get votes cast by a specific user."""
    try:
        votes = vote_crud.get_by_user(
            db=db, 
            user_id=user_id, 
            skip=skip, 
            limit=limit
        )
        
        total = vote_crud.count_by_user(db=db, user_id=user_id)
        
        vote_responses = [VoteResponse.model_validate(vote) for vote in votes]
        
        return paginated_response(
            data=vote_responses,
            page=(skip // limit) + 1,
            per_page=limit,
            total=total,
            message=f"Votes by user {user_id} retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting user votes {user_id}: {e}")
        return error_response(
            message="Failed to retrieve user votes",
            status_code=500,
            error="internal_error"
        )


@router.get("/anonymous/{anon_id}", response_model=dict)
async def get_anonymous_votes(
    anon_id: str = Path(..., description="Anonymous ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get votes cast by an anonymous user."""
    try:
        votes = vote_crud.get_by_anonymous(
            db=db, 
            anon_id=anon_id, 
            skip=skip, 
            limit=limit
        )
        
        total = vote_crud.count_by_anonymous(db=db, anon_id=anon_id)
        
        vote_responses = [VoteResponse.model_validate(vote) for vote in votes]
        
        return paginated_response(
            data=vote_responses,
            page=(skip // limit) + 1,
            per_page=limit,
            total=total,
            message=f"Votes by anonymous user {anon_id} retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting anonymous votes {anon_id}: {e}")
        return error_response(
            message="Failed to retrieve anonymous votes",
            status_code=500,
            error="internal_error"
        )


@router.get("/{vote_id}", response_model=dict)
async def get_vote(
    vote_id: UUID = Path(..., description="Vote ID"),
    db: Session = Depends(get_db)
):
    """Get a specific vote by ID."""
    try:
        vote = vote_crud.get(db=db, vote_id=vote_id)
        
        if not vote:
            return not_found_response(resource="Vote", identifier=str(vote_id))
        
        vote_response = VoteResponse.model_validate(vote)
        
        return success_response(
            data=vote_response,
            message="Vote retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting vote {vote_id}: {e}")
        return error_response(
            message="Failed to retrieve vote",
            status_code=500,
            error="internal_error"
        )


@router.delete("/{vote_id}", response_model=dict)
async def delete_vote(
    vote_id: UUID = Path(..., description="Vote ID"),
    db: Session = Depends(get_db),
    current_user: Optional[UserResponse] = Depends(get_current_user)
):
    """Delete a vote."""
    try:
        # Get vote
        vote = vote_crud.get(db=db, vote_id=vote_id)
        if not vote:
            return not_found_response(resource="Vote", identifier=str(vote_id))
        
        # Check authorization (only voter can delete their vote)
        if current_user:
            if vote.user_id != current_user.id:
                return error_response(
                    message="You can only delete your own votes",
                    status_code=403,
                    error="forbidden"
                )
        else:
            # For anonymous users, we'd need to check anon_id
            # This is a simplified check
            return error_response(
                message="Anonymous votes cannot be deleted",
                status_code=403,
                error="forbidden"
            )
        
        success = vote_crud.delete(db=db, vote_id=vote_id)
        
        if not success:
            return not_found_response(resource="Vote", identifier=str(vote_id))
        
        # Update poll vote counts
        poll_crud.update_vote_counts(db=db, poll_id=vote.poll_id)
        
        return deleted_response(message="Vote deleted successfully")
        
    except Exception as e:
        logger.error(f"Error deleting vote {vote_id}: {e}")
        return error_response(
            message="Failed to delete vote",
            status_code=500,
            error="internal_error"
        )


@router.get("/", response_model=dict)
async def get_votes(
    skip: int = Query(0, ge=0, description="Number of votes to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of votes to return"),
    poll_id: Optional[UUID] = Query(None, description="Filter by poll ID"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db)
):
    """Get list of votes with pagination."""
    try:
        votes = vote_crud.get_multiple(
            db=db, 
            skip=skip, 
            limit=limit,
            poll_id=poll_id,
            user_id=user_id
        )
        
        total = vote_crud.count(db=db, poll_id=poll_id, user_id=user_id)
        
        vote_responses = [VoteResponse.model_validate(vote) for vote in votes]
        
        return paginated_response(
            data=vote_responses,
            page=(skip // limit) + 1,
            per_page=limit,
            total=total,
            message="Votes retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting votes: {e}")
        return error_response(
            message="Failed to retrieve votes",
            status_code=500,
            error="internal_error"
        )
