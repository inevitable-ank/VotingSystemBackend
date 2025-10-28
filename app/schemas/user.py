from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: Optional[EmailStr] = Field(None, description="Email address")


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(..., min_length=6, max_length=100, description="Password")
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must contain only letters, numbers, underscores, and hyphens')
        return v.lower()


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6, max_length=100)


class UserResponse(UserBase):
    """Schema for user response."""
    id: str
    is_active: bool
    is_verified: bool
    created_at: str
    updated_at: str
    last_login: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True, json_encoders={UUID: str})


class UserLogin(BaseModel):
    """Schema for user login."""
    username_or_email: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class UserProfile(BaseModel):
    """Schema for user profile."""
    id: str
    username: str
    email: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: str
    polls_count: int = 0
    votes_count: int = 0
    likes_count: int = 0
    
    model_config = ConfigDict(from_attributes=True, json_encoders={UUID: str})


class AnonymousUser(BaseModel):
    """Schema for anonymous user."""
    anon_id: str = Field(..., description="Anonymous user ID")
    session_token: Optional[str] = Field(None, description="Session token")


class UserStats(BaseModel):
    """Schema for user statistics."""
    total_polls: int = 0
    total_votes: int = 0
    total_likes: int = 0
    polls_created_today: int = 0
    votes_cast_today: int = 0
    likes_given_today: int = 0


class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, max_length=100, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserPreferences(BaseModel):
    """Schema for user preferences."""
    email_notifications: bool = True
    poll_notifications: bool = True
    vote_notifications: bool = False
    like_notifications: bool = False
    public_profile: bool = True
    show_email: bool = False

