from pydantic import BaseModel, Field, validator, ConfigDict, computed_field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class OptionBase(BaseModel):
    """Base option schema."""
    text: str = Field(..., min_length=1, max_length=100, description="Option text")
    position: int = Field(0, ge=0, description="Option position")
    
    @validator('text')
    def validate_text(cls, v):
        """Validate option text."""
        if not v.strip():
            raise ValueError('Option text cannot be empty')
        return v.strip()


class OptionCreate(OptionBase):
    """Schema for creating an option."""
    pass


class OptionUpdate(BaseModel):
    """Schema for updating an option."""
    text: Optional[str] = Field(None, min_length=1, max_length=100)
    position: Optional[int] = Field(None, ge=0)


class OptionResponse(OptionBase):
    """Schema for option response."""
    id: UUID
    poll_id: UUID
    vote_count: int
    
    @computed_field
    @property
    def percentage(self) -> float:
        """Calculate vote percentage."""
        # This will be calculated based on the poll's total_votes
        # For now, return 0.0 as it will be calculated by the model
        return 0.0
    
    model_config = ConfigDict(from_attributes=True, json_encoders={UUID: str})


class OptionStats(BaseModel):
    """Schema for option statistics."""
    id: UUID
    text: str
    vote_count: int
    percentage: float
    votes_over_time: List[dict]
    voter_demographics: dict


class OptionVote(BaseModel):
    """Schema for voting on an option."""
    option_id: UUID = Field(..., description="Option ID to vote for")
    
    @validator('option_id')
    def validate_option_id(cls, v):
        """Validate option ID."""
        if not v:
            raise ValueError('Option ID is required')
        return v


class MultipleOptionVote(BaseModel):
    """Schema for voting on multiple options."""
    option_ids: List[UUID] = Field(..., min_items=1, max_items=5, description="Option IDs to vote for")
    
    @validator('option_ids')
    def validate_option_ids(cls, v):
        """Validate option IDs."""
        if not v:
            raise ValueError('At least one option ID is required')
        
        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError('Option IDs must be unique')
        
        return v
