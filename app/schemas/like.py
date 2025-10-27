from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from uuid import UUID


class LikeBase(BaseModel):
    """Base like schema."""
    poll_id: UUID = Field(..., description="Poll ID")
    
    @validator('poll_id')
    def validate_poll_id(cls, v):
        """Validate poll ID."""
        if not v:
            raise ValueError('Poll ID is required')
        return v


class LikeCreate(LikeBase):
    """Schema for creating a like."""
    anon_id: Optional[str] = Field(None, description="Anonymous user ID")
    ip_address: Optional[str] = Field(None, description="IP address")


class LikeResponse(LikeBase):
    """Schema for like response."""
    id: UUID
    user_id: Optional[UUID] = None
    anon_id: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class LikeStats(BaseModel):
    """Schema for like statistics."""
    total_likes: int
    likes_over_time: list[dict]
    unique_likers: int
    anonymous_likes: int
    authenticated_likes: int


class LikeAnalytics(BaseModel):
    """Schema for like analytics."""
    poll_id: UUID
    total_likes: int
    likes_by_hour: list[dict]
    likes_by_day: list[dict]
    liker_geography: dict
    device_types: dict
    browsers: dict


class LikeHistory(BaseModel):
    """Schema for like history."""
    likes: list[LikeResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool


class LikeValidation(BaseModel):
    """Schema for like validation."""
    can_like: bool
    reason: Optional[str] = None
    has_liked: bool
    poll_active: bool
    poll_exists: bool


class LikeSummary(BaseModel):
    """Schema for like summary."""
    poll_id: UUID
    user_id: Optional[UUID] = None
    anon_id: Optional[str] = None
    total_likes_given: int
    polls_liked: list[UUID]
    first_like_at: datetime
    last_like_at: datetime
    is_anonymous: bool


class LikeToggle(BaseModel):
    """Schema for toggling a like."""
    poll_id: UUID = Field(..., description="Poll ID")
    action: str = Field(..., description="Action: 'like' or 'unlike'")
    
    @validator('action')
    def validate_action(cls, v):
        """Validate action."""
        if v not in ['like', 'unlike']:
            raise ValueError('Action must be "like" or "unlike"')
        return v


class LikeStatus(BaseModel):
    """Schema for like status."""
    poll_id: UUID
    has_liked: bool
    likes_count: int
    can_like: bool
    reason: Optional[str] = None
