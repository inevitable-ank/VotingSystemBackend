from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.db import Base


class Like(Base):
    """Like model for tracking poll likes."""
    
    __tablename__ = "likes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    poll_id = Column(UUID(as_uuid=True), ForeignKey("polls.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    anon_id = Column(String(255), nullable=True, index=True)  # For anonymous users
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    poll = relationship("Poll", back_populates="likes")
    user = relationship("User", back_populates="likes")
    
    # Constraints - ensure one like per user per poll
    __table_args__ = (
        UniqueConstraint('poll_id', 'user_id', name='unique_user_poll_like'),
        UniqueConstraint('poll_id', 'anon_id', name='unique_anon_poll_like'),
    )
    
    def __repr__(self):
        return f"<Like(id={self.id}, poll_id={self.poll_id}, user_id={self.user_id})>"
    
    def to_dict(self):
        """Convert like to dictionary."""
        return {
            "id": str(self.id),
            "poll_id": str(self.poll_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "anon_id": self.anon_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @property
    def liker_identifier(self) -> str:
        """Get liker identifier (user_id or anon_id)."""
        return str(self.user_id) if self.user_id else self.anon_id
    
    @property
    def is_anonymous(self) -> bool:
        """Check if like is from anonymous user."""
        return self.user_id is None and self.anon_id is not None

