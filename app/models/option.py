from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.db import Base


class Option(Base):
    """Poll option model."""
    
    __tablename__ = "options"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    poll_id = Column(UUID(as_uuid=True), ForeignKey("polls.id"), nullable=False, index=True)
    text = Column(String(100), nullable=False)
    position = Column(Integer, nullable=False, default=0)
    
    # Denormalized count for performance
    vote_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    poll = relationship("Poll", back_populates="options")
    votes = relationship("Vote", back_populates="option", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('poll_id', 'position', name='unique_poll_position'),
    )
    
    def __repr__(self):
        return f"<Option(id={self.id}, text={self.text[:30]}...)>"
    
    def to_dict(self):
        """Convert option to dictionary."""
        percentage = 0
        if self.poll and self.poll.total_votes > 0:
            percentage = (self.vote_count / self.poll.total_votes) * 100
        
        return {
            "id": str(self.id),
            "poll_id": str(self.poll_id),
            "text": self.text,
            "position": self.position,
            "vote_count": self.vote_count,
            "percentage": round(percentage, 2)
        }
    
    def increment_votes(self):
        """Increment vote count."""
        self.vote_count += 1
    
    def decrement_votes(self):
        """Decrement vote count."""
        if self.vote_count > 0:
            self.vote_count -= 1

