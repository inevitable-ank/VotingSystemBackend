from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.db import Base


class Poll(Base):
    """Poll model for storing poll information."""
    
    __tablename__ = "polls"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    slug = Column(String(250), unique=True, nullable=False, index=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    allow_multiple = Column(Boolean, default=False, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Denormalized counts for performance
    total_votes = Column(Integer, default=0, nullable=False)
    likes_count = Column(Integer, default=0, nullable=False)
    views_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    author = relationship("User", back_populates="polls")
    options = relationship("Option", back_populates="poll", cascade="all, delete-orphan", order_by="Option.position")
    votes = relationship("Vote", back_populates="poll", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="poll", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Poll(id={self.id}, title={self.title[:50]}...)>"
    
    @property
    def is_expired(self) -> bool:
        """Check if poll has expired."""
        if not self.expires_at:
            return False
        return self.expires_at < func.now()
    
    @property
    def can_vote(self) -> bool:
        """Check if poll can accept votes."""
        return self.is_active and not self.is_expired
    
    def to_dict(self, include_options=True, include_author=True):
        """Convert poll to dictionary."""
        data = {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "slug": self.slug,
            "is_active": self.is_active,
            "allow_multiple": self.allow_multiple,
            "is_public": self.is_public,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "total_votes": self.total_votes,
            "likes_count": self.likes_count,
            "views_count": self.views_count,
            "can_vote": self.can_vote,
            "is_expired": self.is_expired
        }
        
        if include_author and self.author:
            data["author"] = {
                "id": str(self.author.id),
                "username": self.author.username
            }
        
        if include_options and self.options:
            data["options"] = [option.to_dict() for option in self.options]
        
        return data
    
    def increment_views(self):
        """Increment view count."""
        self.views_count += 1
    
    def update_vote_counts(self):
        """Update denormalized vote counts."""
        self.total_votes = sum(option.vote_count for option in self.options)
    
    def update_likes_count(self):
        """Update denormalized likes count."""
        self.likes_count = len(self.likes)

