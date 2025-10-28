from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class PollBase(BaseModel):
    """Base poll schema."""
    title: str = Field(..., min_length=3, max_length=200, description="Poll title")
    description: Optional[str] = Field(None, max_length=1000, description="Poll description")
    allow_multiple: bool = Field(False, description="Allow multiple votes")
    is_public: bool = Field(True, description="Make poll public")
    expires_at: Optional[datetime] = Field(None, description="Poll expiration date")
    
    @validator('title')
    def validate_title(cls, v):
        """Validate poll title."""
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        """Validate poll description."""
        if v is not None and not v.strip():
            return None
        return v.strip() if v else None


class PollCreate(PollBase):
    """Schema for creating a poll."""
    options: List[str] = Field(..., min_items=2, max_items=10, description="Poll options")
    
    @validator('options')
    def validate_options(cls, v):
        """Validate poll options."""
        if not v:
            raise ValueError('At least 2 options are required')
        
        # Remove empty options and validate
        valid_options = [opt.strip() for opt in v if opt.strip()]
        if len(valid_options) < 2:
            raise ValueError('At least 2 valid options are required')
        
        # Check for duplicates
        if len(valid_options) != len(set(valid_options)):
            raise ValueError('Options must be unique')
        
        # Validate option length
        for opt in valid_options:
            if len(opt) > 100:
                raise ValueError('Option text cannot exceed 100 characters')
        
        return valid_options


class PollUpdate(BaseModel):
    """Schema for updating a poll."""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    expires_at: Optional[datetime] = None


class PollResponse(PollBase):
    """Schema for poll response."""
    id: UUID
    slug: str
    author_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    total_votes: int
    likes_count: int
    views_count: int
    can_vote: bool
    is_expired: bool
    
    class Config:
        from_attributes = True


class PollDetail(PollResponse):
    """Schema for detailed poll response."""
    options: List['OptionResponse'] = []
    author: Optional['UserResponse'] = None


class PollList(BaseModel):
    """Schema for poll list response."""
    polls: List[PollResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool


class PollStats(BaseModel):
    """Schema for poll statistics."""
    total_polls: int
    active_polls: int
    expired_polls: int
    total_votes: int
    total_likes: int
    total_views: int
    polls_created_today: int
    votes_cast_today: int


class PollSearch(BaseModel):
    """Schema for poll search."""
    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    category: Optional[str] = Field(None, description="Poll category")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")


class PollAnalytics(BaseModel):
    """Schema for poll analytics."""
    poll_id: UUID
    total_votes: int
    unique_voters: int
    votes_by_option: List[dict]
    votes_over_time: List[dict]
    voter_demographics: dict
    engagement_metrics: dict


# Import here to avoid circular imports
from app.schemas.option import OptionResponse
from app.schemas.user import UserResponse

# Update forward references
PollDetail.model_rebuild()

