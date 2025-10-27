from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
import logging

from app.core.db import get_db
from app.crud.user import user_crud
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserLogin, UserProfile
from app.utils.response_helper import (
    success_response, error_response, paginated_response, 
    created_response, updated_response, deleted_response, not_found_response
)
from app.utils.exceptions import UserNotFoundError, ValidationError, ConflictError
from app.core.security import get_password_hash, verify_password, create_access_token

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=dict)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    try:
        # Check if username already exists
        existing_user = user_crud.get_by_username(db=db, username=user_data.username)
        if existing_user:
            return error_response(
                message="Username already exists",
                status_code=409,
                error="conflict_error"
            )
        
        # Check if email already exists
        if user_data.email:
            existing_email = user_crud.get_by_email(db=db, email=user_data.email)
            if existing_email:
                return error_response(
                    message="Email already exists",
                    status_code=409,
                    error="conflict_error"
                )
        
        # Create user
        user = user_crud.create(db=db, user_data=user_data)
        
        # Create access token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        user_response = UserResponse.from_orm(user)
        
        return created_response(
            data={
                "user": user_response,
                "access_token": access_token,
                "token_type": "bearer"
            },
            message="User registered successfully"
        )
        
    except ValidationError as e:
        return error_response(
            message=str(e),
            status_code=422,
            error="validation_error"
        )
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        return error_response(
            message="Failed to register user",
            status_code=500,
            error="internal_error"
        )


@router.post("/login", response_model=dict)
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user."""
    try:
        # Get user by username or email
        user = user_crud.get_by_username_or_email(db=db, identifier=login_data.username_or_email)
        
        if not user:
            return error_response(
                message="Invalid credentials",
                status_code=401,
                error="authentication_error"
            )
        
        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            return error_response(
                message="Invalid credentials",
                status_code=401,
                error="authentication_error"
            )
        
        # Check if user is active
        if not user.is_active:
            return error_response(
                message="Account is deactivated",
                status_code=403,
                error="account_deactivated"
            )
        
        # Update last login
        user_crud.update_last_login(db=db, user_id=user.id)
        
        # Create access token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        user_response = UserResponse.from_orm(user)
        
        return success_response(
            data={
                "user": user_response,
                "access_token": access_token,
                "token_type": "bearer"
            },
            message="Login successful"
        )
        
    except Exception as e:
        logger.error(f"Error logging in user: {e}")
        return error_response(
            message="Failed to login",
            status_code=500,
            error="internal_error"
        )


@router.get("/me", response_model=dict)
async def get_current_user_profile(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get current user profile."""
    try:
        # This would be implemented with proper authentication
        # For now, return a placeholder response
        return error_response(
            message="Authentication required",
            status_code=401,
            error="authentication_error"
        )
        
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return error_response(
            message="Failed to get user profile",
            status_code=500,
            error="internal_error"
        )


@router.put("/me", response_model=dict)
async def update_current_user_profile(
    user_data: UserUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update current user profile."""
    try:
        # This would be implemented with proper authentication
        # For now, return a placeholder response
        return error_response(
            message="Authentication required",
            status_code=401,
            error="authentication_error"
        )
        
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        return error_response(
            message="Failed to update user profile",
            status_code=500,
            error="internal_error"
        )


@router.get("/", response_model=dict)
async def get_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of users to return"),
    search: Optional[str] = Query(None, description="Search by username"),
    db: Session = Depends(get_db)
):
    """Get list of users with pagination."""
    try:
        users = user_crud.get_multiple(
            db=db, 
            skip=skip, 
            limit=limit,
            search=search
        )
        
        total = user_crud.count(db=db)
        
        user_responses = [UserResponse.from_orm(user) for user in users]
        
        return paginated_response(
            data=user_responses,
            page=(skip // limit) + 1,
            per_page=limit,
            total=total,
            message="Users retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return error_response(
            message="Failed to retrieve users",
            status_code=500,
            error="internal_error"
        )


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: UUID = Path(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get a specific user by ID."""
    try:
        user = user_crud.get(db=db, user_id=user_id)
        
        if not user:
            return not_found_response(resource="User", identifier=str(user_id))
        
        user_response = UserResponse.from_orm(user)
        
        return success_response(
            data=user_response,
            message="User retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return error_response(
            message="Failed to retrieve user",
            status_code=500,
            error="internal_error"
        )


@router.get("/username/{username}", response_model=dict)
async def get_user_by_username(
    username: str = Path(..., description="Username"),
    db: Session = Depends(get_db)
):
    """Get a specific user by username."""
    try:
        user = user_crud.get_by_username(db=db, username=username)
        
        if not user:
            return not_found_response(resource="User", identifier=username)
        
        user_response = UserResponse.from_orm(user)
        
        return success_response(
            data=user_response,
            message="User retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting user by username {username}: {e}")
        return error_response(
            message="Failed to retrieve user",
            status_code=500,
            error="internal_error"
        )


@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: UUID = Path(..., description="User ID"),
    user_data: UserUpdate = None,
    db: Session = Depends(get_db)
):
    """Update a user."""
    try:
        # Check if user exists
        user = user_crud.get(db=db, user_id=user_id)
        if not user:
            return not_found_response(resource="User", identifier=str(user_id))
        
        updated_user = user_crud.update(
            db=db,
            user_id=user_id,
            user_data=user_data
        )
        
        if not updated_user:
            return not_found_response(resource="User", identifier=str(user_id))
        
        user_response = UserResponse.from_orm(updated_user)
        
        return updated_response(
            data=user_response,
            message="User updated successfully"
        )
        
    except ValidationError as e:
        return error_response(
            message=str(e),
            status_code=422,
            error="validation_error"
        )
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        return error_response(
            message="Failed to update user",
            status_code=500,
            error="internal_error"
        )


@router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: UUID = Path(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Delete a user."""
    try:
        # Check if user exists
        user = user_crud.get(db=db, user_id=user_id)
        if not user:
            return not_found_response(resource="User", identifier=str(user_id))
        
        success = user_crud.delete(db=db, user_id=user_id)
        
        if not success:
            return not_found_response(resource="User", identifier=str(user_id))
        
        return deleted_response(message="User deleted successfully")
        
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        return error_response(
            message="Failed to delete user",
            status_code=500,
            error="internal_error"
        )


@router.post("/{user_id}/activate", response_model=dict)
async def activate_user(
    user_id: UUID = Path(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Activate a user."""
    try:
        # Check if user exists
        user = user_crud.get(db=db, user_id=user_id)
        if not user:
            return not_found_response(resource="User", identifier=str(user_id))
        
        success = user_crud.activate(db=db, user_id=user_id)
        
        if not success:
            return not_found_response(resource="User", identifier=str(user_id))
        
        return success_response(
            message="User activated successfully"
        )
        
    except Exception as e:
        logger.error(f"Error activating user {user_id}: {e}")
        return error_response(
            message="Failed to activate user",
            status_code=500,
            error="internal_error"
        )


@router.post("/{user_id}/deactivate", response_model=dict)
async def deactivate_user(
    user_id: UUID = Path(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Deactivate a user."""
    try:
        # Check if user exists
        user = user_crud.get(db=db, user_id=user_id)
        if not user:
            return not_found_response(resource="User", identifier=str(user_id))
        
        success = user_crud.deactivate(db=db, user_id=user_id)
        
        if not success:
            return not_found_response(resource="User", identifier=str(user_id))
        
        return success_response(
            message="User deactivated successfully"
        )
        
    except Exception as e:
        logger.error(f"Error deactivating user {user_id}: {e}")
        return error_response(
            message="Failed to deactivate user",
            status_code=500,
            error="internal_error"
        )


@router.get("/{user_id}/polls", response_model=dict)
async def get_user_polls(
    user_id: UUID = Path(..., description="User ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get polls created by a user."""
    try:
        # Check if user exists
        user = user_crud.get(db=db, user_id=user_id)
        if not user:
            return not_found_response(resource="User", identifier=str(user_id))
        
        polls = user_crud.get_user_polls(db=db, user_id=user_id, skip=skip, limit=limit)
        
        return success_response(
            data=polls,
            message=f"Polls for user {user.username} retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting user polls {user_id}: {e}")
        return error_response(
            message="Failed to retrieve user polls",
            status_code=500,
            error="internal_error"
        )
