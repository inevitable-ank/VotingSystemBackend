from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from app.models.option import Option
from app.models.poll import Poll
from app.schemas.option import OptionCreate, OptionUpdate
from app.utils.exceptions import OptionNotFoundError, ValidationError, ConflictError

logger = logging.getLogger(__name__)


class OptionCRUD:
    """CRUD operations for Option model."""
    
    def create(self, db: Session, poll_id: UUID, option_data: OptionCreate) -> Option:
        """
        Create a new option for a poll.
        
        Args:
            db: Database session
            poll_id: Poll ID
            option_data: Option creation data
            
        Returns:
            Option: Created option
        """
        # Verify poll exists
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            raise ValidationError(f"Poll with ID {poll_id} not found")
        
        # Check if poll allows new options (for future feature)
        if not poll.is_active:
            raise ValidationError("Cannot add options to inactive poll")
        
        # Get next position
        max_position = db.query(func.max(Option.position)).filter(
            Option.poll_id == poll_id
        ).scalar() or -1
        
        db_option = Option(
            poll_id=poll_id,
            text=option_data.text,
            position=max_position + 1
        )
        
        db.add(db_option)
        db.commit()
        db.refresh(db_option)
        
        logger.info(f"Option created: {db_option.text} for poll {poll_id}")
        return db_option
    
    def get(self, db: Session, option_id: UUID) -> Optional[Option]:
        """Get option by ID."""
        return db.query(Option).filter(Option.id == option_id).first()
    
    def get_by_poll(self, db: Session, poll_id: UUID) -> List[Option]:
        """Get all options for a poll."""
        return db.query(Option).filter(
            Option.poll_id == poll_id
        ).order_by(Option.position).all()
    
    def get_with_poll(self, db: Session, option_id: UUID) -> Optional[Option]:
        """Get option with poll details."""
        return db.query(Option).options(joinedload(Option.poll)).filter(
            Option.id == option_id
        ).first()
    
    def update(self, db: Session, option_id: UUID, option_data: OptionUpdate) -> Optional[Option]:
        """
        Update option.
        
        Args:
            db: Database session
            option_id: Option ID
            option_data: Update data
            
        Returns:
            Option: Updated option or None if not found
        """
        db_option = self.get(db, option_id)
        if not db_option:
            return None
        
        # Check if poll is active
        if not db_option.poll.is_active:
            raise ValidationError("Cannot modify options of inactive poll")
        
        # Update fields
        update_data = option_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_option, field, value)
        
        db.commit()
        db.refresh(db_option)
        
        logger.info(f"Option updated: {db_option.text} (ID: {db_option.id})")
        return db_option
    
    def delete(self, db: Session, option_id: UUID) -> bool:
        """
        Delete option.
        
        Args:
            db: Database session
            option_id: Option ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        db_option = self.get(db, option_id)
        if not db_option:
            return False
        
        # Check if poll is active
        if not db_option.poll.is_active:
            raise ValidationError("Cannot delete options of inactive poll")
        
        # Check if option has votes
        if db_option.vote_count > 0:
            raise ValidationError("Cannot delete option with existing votes")
        
        # Check minimum options requirement
        poll_options = self.get_by_poll(db, db_option.poll_id)
        if len(poll_options) <= 2:
            raise ValidationError("Poll must have at least 2 options")
        
        db.delete(db_option)
        db.commit()
        
        logger.info(f"Option deleted: {db_option.text} (ID: {db_option.id})")
        return True
    
    def reorder(self, db: Session, poll_id: UUID, option_positions: Dict[UUID, int]) -> bool:
        """
        Reorder options for a poll.
        
        Args:
            db: Database session
            poll_id: Poll ID
            option_positions: Dictionary mapping option IDs to new positions
            
        Returns:
            bool: True if successful
        """
        # Verify poll exists and is active
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            raise ValidationError(f"Poll with ID {poll_id} not found")
        
        if not poll.is_active:
            raise ValidationError("Cannot reorder options of inactive poll")
        
        # Update positions
        for option_id, position in option_positions.items():
            option = self.get(db, option_id)
            if option and option.poll_id == poll_id:
                option.position = position
        
        db.commit()
        
        logger.info(f"Options reordered for poll {poll_id}")
        return True
    
    def increment_votes(self, db: Session, option_id: UUID) -> bool:
        """Increment option vote count."""
        db_option = self.get(db, option_id)
        if not db_option:
            return False
        
        db_option.increment_votes()
        db.commit()
        
        return True
    
    def decrement_votes(self, db: Session, option_id: UUID) -> bool:
        """Decrement option vote count."""
        db_option = self.get(db, option_id)
        if not db_option:
            return False
        
        db_option.decrement_votes()
        db.commit()
        
        return True
    
    def get_stats(self, db: Session, option_id: UUID) -> Dict[str, Any]:
        """Get option statistics."""
        option = self.get_with_poll(db, option_id)
        if not option:
            raise OptionNotFoundError(str(option_id))
        
        total_poll_votes = option.poll.total_votes
        percentage = (option.vote_count / total_poll_votes * 100) if total_poll_votes > 0 else 0
        
        return {
            "option_id": str(option_id),
            "poll_id": str(option.poll_id),
            "text": option.text,
            "position": option.position,
            "vote_count": option.vote_count,
            "percentage": round(percentage, 2),
            "poll_total_votes": total_poll_votes,
            "poll_title": option.poll.title
        }
    
    def get_top_options(self, db: Session, poll_id: UUID, limit: int = 5) -> List[Option]:
        """Get top options by vote count for a poll."""
        return db.query(Option).filter(
            Option.poll_id == poll_id
        ).order_by(desc(Option.vote_count)).limit(limit).all()
    
    def search(self, db: Session, query: str, poll_id: Optional[UUID] = None) -> List[Option]:
        """Search options by text."""
        query_filter = Option.text.ilike(f"%{query}%")
        
        if poll_id:
            query_filter = and_(query_filter, Option.poll_id == poll_id)
        
        return db.query(Option).filter(query_filter).all()
    
    def get_by_position_range(self, db: Session, poll_id: UUID, 
                             start_pos: int, end_pos: int) -> List[Option]:
        """Get options within position range."""
        return db.query(Option).filter(
            and_(
                Option.poll_id == poll_id,
                Option.position >= start_pos,
                Option.position <= end_pos
            )
        ).order_by(Option.position).all()
    
    def validate_option_belongs_to_poll(self, db: Session, option_id: UUID, poll_id: UUID) -> bool:
        """Validate that option belongs to poll."""
        option = self.get(db, option_id)
        return option is not None and option.poll_id == poll_id


# Create instance
option_crud = OptionCRUD()
