from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class VoteBase(BaseModel):
    """Base vote schema."""
    poll_id: UUID = Field(..., description="Poll ID")
    option_id: UUID = Field(..., description="Option ID")
    
    @validator('poll_id')
    def validate_poll_id(cls, v):
        """Validate poll ID."""
        if not v:
            raise ValueError('Poll ID is required')
        return v
    
    @validator('option_id')
    def validate_option_id(cls, v):
        """Validate option ID."""
        if not v:
            raise ValueError('Option ID is required')
        return v


class VoteCreate(VoteBase):
    """Schema for creating a vote."""
    anon_id: Optional[str] = Field(None, description="Anonymous user ID")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")


class MultipleVoteCreate(BaseModel):
    """Schema for creating multiple votes."""
    poll_id: UUID = Field(..., description="Poll ID")
    option_ids: list[UUID] = Field(..., min_items=1, max_items=5, description="Option IDs")
    anon_id: Optional[str] = Field(None, description="Anonymous user ID")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    
    @validator('option_ids')
    def validate_option_ids(cls, v):
        """Validate option IDs."""
        if not v:
            raise ValueError('At least one option ID is required')
        
        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError('Option IDs must be unique')
        
        return v


class VoteResponse(VoteBase):
    """Schema for vote response."""
    id: UUID
    user_id: Optional[UUID] = None
    anon_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    option_text: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True, json_encoders={UUID: str})


class VoteUpdate(BaseModel):
    """Schema for updating a vote."""
    option_id: UUID = Field(..., description="New option ID")


class VoteStats(BaseModel):
    """Schema for vote statistics."""
    total_votes: int
    votes_by_option: dict
    votes_over_time: list[dict]
    unique_voters: int
    anonymous_votes: int
    authenticated_votes: int


class VoteAnalytics(BaseModel):
    """Schema for vote analytics."""
    poll_id: UUID
    total_votes: int
    votes_by_hour: list[dict]
    votes_by_day: list[dict]
    voter_geography: dict
    device_types: dict
    browsers: dict


class VoteHistory(BaseModel):
    """Schema for vote history."""
    votes: list[VoteResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool


class VoteValidation(BaseModel):
    """Schema for vote validation."""
    can_vote: bool
    reason: Optional[str] = None
    has_voted: bool
    voted_option_id: Optional[UUID] = None
    poll_expired: bool
    poll_active: bool


class VoteSummary(BaseModel):
    """Schema for vote summary."""
    poll_id: UUID
    user_id: Optional[UUID] = None
    anon_id: Optional[str] = None
    total_votes_cast: int
    options_voted: list[UUID]
    first_vote_at: datetime
    last_vote_at: datetime
    is_anonymous: bool

