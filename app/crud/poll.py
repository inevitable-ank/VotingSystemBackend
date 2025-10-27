from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc, text
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from app.models.poll import Poll
from app.models.option import Option
from app.schemas.poll import PollCreate, PollUpdate
from app.core.security import generate_poll_slug
from app.utils.exceptions import PollNotFoundError, ValidationError, ConflictError

logger = logging.getLogger(__name__)


class PollCRUD:
    """CRUD operations for Poll model."""
    
    def create(self, db: Session, poll_data: PollCreate, author_id: Optional[UUID] = None) -> Poll:
        """
        Create a new poll.
        
        Args:
            db: Database session
            poll_data: Poll creation data
            author_id: Optional author ID
            
        Returns:
            Poll: Created poll
        """
        # Generate unique slug
        slug = generate_poll_slug(poll_data.title)
        
        # Create poll
        db_poll = Poll(
            title=poll_data.title,
            description=poll_data.description,
            slug=slug,
            author_id=author_id,
            allow_multiple=poll_data.allow_multiple,
            is_public=poll_data.is_public,
            expires_at=poll_data.expires_at
        )
        
        db.add(db_poll)
        db.flush()  # Get the poll ID
        
        # Create options
        for i, option_text in enumerate(poll_data.options):
            option = Option(
                poll_id=db_poll.id,
                text=option_text,
                position=i
            )
            db.add(option)
        
        db.commit()
        db.refresh(db_poll)
        
        logger.info(f"Poll created: {db_poll.title} (ID: {db_poll.id})")
        return db_poll
    
    def get(self, db: Session, poll_id: UUID) -> Optional[Poll]:
        """Get poll by ID."""
        return db.query(Poll).filter(Poll.id == poll_id).first()
    
    def get_by_slug(self, db: Session, slug: str) -> Optional[Poll]:
        """Get poll by slug."""
        return db.query(Poll).filter(Poll.slug == slug).first()
    
    def get_with_options(self, db: Session, poll_id: UUID) -> Optional[Poll]:
        """Get poll with options."""
        return db.query(Poll).options(joinedload(Poll.options)).filter(Poll.id == poll_id).first()
    
    def get_with_details(self, db: Session, poll_id: UUID) -> Optional[Poll]:
        """Get poll with all details."""
        return db.query(Poll).options(
            joinedload(Poll.options),
            joinedload(Poll.author),
            joinedload(Poll.votes),
            joinedload(Poll.likes)
        ).filter(Poll.id == poll_id).first()
    
    def get_multiple(self, db: Session, skip: int = 0, limit: int = 20, 
                    include_expired: bool = False) -> List[Poll]:
        """Get multiple polls with pagination."""
        query = db.query(Poll)
        
        if not include_expired:
            query = query.filter(
                or_(
                    Poll.expires_at.is_(None),
                    Poll.expires_at > func.now()
                )
            )
        
        return query.order_by(desc(Poll.created_at)).offset(skip).limit(limit).all()
    
    def get_public(self, db: Session, skip: int = 0, limit: int = 20) -> List[Poll]:
        """Get public polls."""
        return db.query(Poll).filter(
            Poll.is_public == True,
            Poll.is_active == True,
            or_(
                Poll.expires_at.is_(None),
                Poll.expires_at > func.now()
            )
        ).order_by(desc(Poll.created_at)).offset(skip).limit(limit).all()
    
    def get_by_author(self, db: Session, author_id: UUID, skip: int = 0, limit: int = 20) -> List[Poll]:
        """Get polls by author."""
        return db.query(Poll).filter(
            Poll.author_id == author_id
        ).order_by(desc(Poll.created_at)).offset(skip).limit(limit).all()
    
    def update(self, db: Session, poll_id: UUID, poll_data: PollUpdate) -> Optional[Poll]:
        """
        Update poll.
        
        Args:
            db: Database session
            poll_id: Poll ID
            poll_data: Update data
            
        Returns:
            Poll: Updated poll or None if not found
        """
        db_poll = self.get(db, poll_id)
        if not db_poll:
            return None
        
        # Update fields
        update_data = poll_data.dict(exclude_unset=True)
        
        # Generate new slug if title changed
        if 'title' in update_data and update_data['title'] != db_poll.title:
            update_data['slug'] = generate_poll_slug(update_data['title'])
        
        for field, value in update_data.items():
            setattr(db_poll, field, value)
        
        db.commit()
        db.refresh(db_poll)
        
        logger.info(f"Poll updated: {db_poll.title} (ID: {db_poll.id})")
        return db_poll
    
    def delete(self, db: Session, poll_id: UUID) -> bool:
        """
        Delete poll.
        
        Args:
            db: Database session
            poll_id: Poll ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        db_poll = self.get(db, poll_id)
        if not db_poll:
            return False
        
        db.delete(db_poll)
        db.commit()
        
        logger.info(f"Poll deleted: {db_poll.title} (ID: {db_poll.id})")
        return True
    
    def increment_views(self, db: Session, poll_id: UUID) -> bool:
        """Increment poll view count."""
        db_poll = self.get(db, poll_id)
        if not db_poll:
            return False
        
        db_poll.increment_views()
        db.commit()
        
        return True
    
    def update_vote_counts(self, db: Session, poll_id: UUID) -> bool:
        """Update poll vote counts."""
        db_poll = self.get_with_options(db, poll_id)
        if not db_poll:
            return False
        
        db_poll.update_vote_counts()
        db.commit()
        
        return True
    
    def update_likes_count(self, db: Session, poll_id: UUID) -> bool:
        """Update poll likes count."""
        db_poll = self.get(db, poll_id)
        if not db_poll:
            return False
        
        db_poll.update_likes_count()
        db.commit()
        
        return True
    
    def search(self, db: Session, query: str, skip: int = 0, limit: int = 20) -> List[Poll]:
        """Search polls by title or description."""
        return db.query(Poll).filter(
            and_(
                Poll.is_public == True,
                or_(
                    Poll.title.ilike(f"%{query}%"),
                    Poll.description.ilike(f"%{query}%")
                )
            )
        ).order_by(desc(Poll.created_at)).offset(skip).limit(limit).all()
    
    def get_trending(self, db: Session, skip: int = 0, limit: int = 20) -> List[Poll]:
        """Get trending polls (by votes and likes)."""
        return db.query(Poll).filter(
            Poll.is_public == True,
            Poll.is_active == True,
            or_(
                Poll.expires_at.is_(None),
                Poll.expires_at > func.now()
            )
        ).order_by(
            desc(Poll.total_votes + Poll.likes_count),
            desc(Poll.created_at)
        ).offset(skip).limit(limit).all()
    
    def get_popular(self, db: Session, skip: int = 0, limit: int = 20) -> List[Poll]:
        """Get popular polls (by views)."""
        return db.query(Poll).filter(
            Poll.is_public == True,
            Poll.is_active == True,
            or_(
                Poll.expires_at.is_(None),
                Poll.expires_at > func.now()
            )
        ).order_by(
            desc(Poll.views_count),
            desc(Poll.created_at)
        ).offset(skip).limit(limit).all()
    
    def get_recent(self, db: Session, skip: int = 0, limit: int = 20) -> List[Poll]:
        """Get recent polls."""
        return db.query(Poll).filter(
            Poll.is_public == True,
            Poll.is_active == True,
            or_(
                Poll.expires_at.is_(None),
                Poll.expires_at > func.now()
            )
        ).order_by(desc(Poll.created_at)).offset(skip).limit(limit).all()
    
    def get_expired(self, db: Session, skip: int = 0, limit: int = 20) -> List[Poll]:
        """Get expired polls."""
        return db.query(Poll).filter(
            Poll.expires_at < func.now()
        ).order_by(desc(Poll.expires_at)).offset(skip).limit(limit).all()
    
    def get_stats(self, db: Session) -> Dict[str, Any]:
        """Get poll statistics."""
        total_polls = db.query(Poll).count()
        active_polls = db.query(Poll).filter(Poll.is_active == True).count()
        expired_polls = db.query(Poll).filter(Poll.expires_at < func.now()).count()
        total_votes = db.query(func.sum(Poll.total_votes)).scalar() or 0
        total_likes = db.query(func.sum(Poll.likes_count)).scalar() or 0
        total_views = db.query(func.sum(Poll.views_count)).scalar() or 0
        
        return {
            "total_polls": total_polls,
            "active_polls": active_polls,
            "expired_polls": expired_polls,
            "total_votes": total_votes,
            "total_likes": total_likes,
            "total_views": total_views,
            "polls_created_today": db.query(Poll).filter(
                func.date(Poll.created_at) == func.current_date()
            ).count(),
            "votes_cast_today": db.query(Poll).filter(
                func.date(Poll.created_at) == func.current_date()
            ).count()
        }
    
    def deactivate(self, db: Session, poll_id: UUID) -> bool:
        """Deactivate poll."""
        db_poll = self.get(db, poll_id)
        if not db_poll:
            return False
        
        db_poll.is_active = False
        db.commit()
        
        logger.info(f"Poll deactivated: {db_poll.title} (ID: {db_poll.id})")
        return True
    
    def activate(self, db: Session, poll_id: UUID) -> bool:
        """Activate poll."""
        db_poll = self.get(db, poll_id)
        if not db_poll:
            return False
        
        db_poll.is_active = True
        db.commit()
        
        logger.info(f"Poll activated: {db_poll.title} (ID: {db_poll.id})")
        return True


# Create instance
poll_crud = PollCRUD()
