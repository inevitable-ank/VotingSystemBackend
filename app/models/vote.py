from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.db import Base


class Vote(Base):
    """Vote model for tracking user votes."""
    
    __tablename__ = "votes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    poll_id = Column(UUID(as_uuid=True), ForeignKey("polls.id"), nullable=False, index=True)
    option_id = Column(UUID(as_uuid=True), ForeignKey("options.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    anon_id = Column(String(255), nullable=True, index=True)  # For anonymous users
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    poll = relationship("Poll", back_populates="votes")
    option = relationship("Option", back_populates="votes")
    user = relationship("User", back_populates="votes")
    
    # Constraints - ensure one vote per user per poll (for single-choice polls)
    __table_args__ = (
        UniqueConstraint('poll_id', 'user_id', name='unique_user_poll_vote'),
        UniqueConstraint('poll_id', 'anon_id', name='unique_anon_poll_vote'),
    )
    
    def __repr__(self):
        return f"<Vote(id={self.id}, poll_id={self.poll_id}, option_id={self.option_id})>"
    
    def to_dict(self):
        """Convert vote to dictionary."""
        return {
            "id": str(self.id),
            "poll_id": str(self.poll_id),
            "option_id": str(self.option_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "anon_id": self.anon_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "option_text": self.option.text if self.option else None
        }
    
    @property
    def voter_identifier(self) -> str:
        """Get voter identifier (user_id or anon_id)."""
        return str(self.user_id) if self.user_id else self.anon_id
    
    @property
    def is_anonymous(self) -> bool:
        """Check if vote is from anonymous user."""
        return self.user_id is None and self.anon_id is not None
