from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from app.models.like import Like
from app.models.poll import Poll
from app.schemas.like import LikeCreate
from app.utils.exceptions import PollNotFoundError, ConflictError

logger = logging.getLogger(__name__)


class LikeCRUD:
    """CRUD operations for Like model."""
    
    def create(self, db: Session, like_data: LikeCreate, user_id: Optional[UUID] = None) -> Like:
        """
        Create a new like.
        
        Args:
            db: Database session
            like_data: Like creation data
            user_id: Optional user ID
            
        Returns:
            Like: Created like
            
        Raises:
            PollNotFoundError: If poll not found
            ConflictError: If user already liked the poll
        """
        # Verify poll exists
        poll = db.query(Poll).filter(Poll.id == like_data.poll_id).first()
        if not poll:
            raise PollNotFoundError(str(like_data.poll_id))
        
        # Check for existing like
        existing_like = self.get_user_like(db, like_data.poll_id, user_id, like_data.anon_id)
        if existing_like:
            raise ConflictError(f"User has already liked poll {like_data.poll_id}")
        
        # Create like
        db_like = Like(
            poll_id=like_data.poll_id,
            user_id=user_id,
            anon_id=like_data.anon_id,
            ip_address=like_data.ip_address
        )
        
        db.add(db_like)
        
        # Update poll likes count
        poll.likes_count += 1
        
        db.commit()
        db.refresh(db_like)
        
        logger.info(f"Like created: {db_like.id} for poll {like_data.poll_id}")
        return db_like
    
    def get(self, db: Session, like_id: UUID) -> Optional[Like]:
        """Get like by ID."""
        return db.query(Like).filter(Like.id == like_id).first()
    
    def get_user_like(self, db: Session, poll_id: UUID, user_id: Optional[UUID] = None, 
                     anon_id: Optional[str] = None) -> Optional[Like]:
        """Get user's like for a poll."""
        query = db.query(Like).filter(Like.poll_id == poll_id)
        
        if user_id:
            query = query.filter(Like.user_id == user_id)
        elif anon_id:
            query = query.filter(Like.anon_id == anon_id)
        else:
            return None
        
        return query.first()
    
    def get_by_poll(self, db: Session, poll_id: UUID, skip: int = 0, limit: int = 100) -> List[Like]:
        """Get all likes for a poll."""
        return db.query(Like).filter(Like.poll_id == poll_id).offset(skip).limit(limit).all()
    
    def get_by_user(self, db: Session, user_id: Optional[UUID] = None, anon_id: Optional[str] = None, 
                   skip: int = 0, limit: int = 100) -> List[Like]:
        """Get all likes by a user."""
        query = db.query(Like)
        
        if user_id:
            query = query.filter(Like.user_id == user_id)
        elif anon_id:
            query = query.filter(Like.anon_id == anon_id)
        else:
            return []
        
        return query.order_by(desc(Like.created_at)).offset(skip).limit(limit).all()
    
    def get_with_details(self, db: Session, like_id: UUID) -> Optional[Like]:
        """Get like with poll and user details."""
        return db.query(Like).options(
            joinedload(Like.poll),
            joinedload(Like.user)
        ).filter(Like.id == like_id).first()
    
    def delete(self, db: Session, like_id: UUID) -> bool:
        """
        Delete like.
        
        Args:
            db: Database session
            like_id: Like ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        db_like = self.get_with_details(db, like_id)
        if not db_like:
            return False
        
        # Update poll likes count
        db_like.poll.likes_count -= 1
        
        db.delete(db_like)
        db.commit()
        
        logger.info(f"Like deleted: {db_like.id} for poll {db_like.poll_id}")
        return True
    
    def delete_user_like(self, db: Session, poll_id: UUID, user_id: Optional[UUID] = None, 
                        anon_id: Optional[str] = None) -> bool:
        """
        Delete user's like for a poll.
        
        Args:
            db: Database session
            poll_id: Poll ID
            user_id: Optional user ID
            anon_id: Optional anonymous ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        db_like = self.get_user_like(db, poll_id, user_id, anon_id)
        if not db_like:
            return False
        
        # Update poll likes count
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if poll:
            poll.likes_count -= 1
        
        db.delete(db_like)
        db.commit()
        
        logger.info(f"User like deleted for poll {poll_id}")
        return True
    
    def toggle_like(self, db: Session, poll_id: UUID, user_id: Optional[UUID] = None, 
                   anon_id: Optional[str] = None, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Toggle like for a poll (like if not liked, unlike if liked).
        
        Args:
            db: Database session
            poll_id: Poll ID
            user_id: Optional user ID
            anon_id: Optional anonymous ID
            ip_address: Optional IP address
            
        Returns:
            Dict: Result with action taken and current like status
        """
        # Verify poll exists
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            raise PollNotFoundError(str(poll_id))
        
        # Check if user already liked
        existing_like = self.get_user_like(db, poll_id, user_id, anon_id)
        
        if existing_like:
            # Unlike
            self.delete_user_like(db, poll_id, user_id, anon_id)
            action = "unliked"
            has_liked = False
        else:
            # Like
            like_data = LikeCreate(
                poll_id=poll_id,
                anon_id=anon_id,
                ip_address=ip_address
            )
            self.create(db, like_data, user_id)
            action = "liked"
            has_liked = True
        
        # Get updated likes count
        updated_poll = db.query(Poll).filter(Poll.id == poll_id).first()
        
        return {
            "action": action,
            "has_liked": has_liked,
            "likes_count": updated_poll.likes_count if updated_poll else 0,
            "poll_id": str(poll_id)
        }
    
    def get_stats(self, db: Session, poll_id: UUID) -> Dict[str, Any]:
        """Get like statistics for a poll."""
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            raise PollNotFoundError(str(poll_id))
        
        likes = self.get_by_poll(db, poll_id)
        
        # Count unique likers
        unique_likers = set()
        anonymous_likes = 0
        authenticated_likes = 0
        
        for like in likes:
            if like.user_id:
                unique_likers.add(str(like.user_id))
                authenticated_likes += 1
            elif like.anon_id:
                unique_likers.add(like.anon_id)
                anonymous_likes += 1
        
        return {
            "poll_id": str(poll_id),
            "total_likes": len(likes),
            "unique_likers": len(unique_likers),
            "anonymous_likes": anonymous_likes,
            "authenticated_likes": authenticated_likes,
            "poll_likes_count": poll.likes_count
        }
    
    def get_user_like_history(self, db: Session, user_id: Optional[UUID] = None, 
                            anon_id: Optional[str] = None, skip: int = 0, limit: int = 50) -> List[Like]:
        """Get user's like history."""
        return self.get_by_user(db, user_id, anon_id, skip, limit)
    
    def get_liked_polls(self, db: Session, user_id: Optional[UUID] = None, 
                       anon_id: Optional[str] = None, skip: int = 0, limit: int = 50) -> List[Poll]:
        """Get polls liked by user."""
        likes = self.get_by_user(db, user_id, anon_id, skip, limit)
        poll_ids = [like.poll_id for like in likes]
        
        if not poll_ids:
            return []
        
        return db.query(Poll).filter(Poll.id.in_(poll_ids)).all()
    
    def validate_like_permission(self, db: Session, poll_id: UUID, user_id: Optional[UUID] = None, 
                               anon_id: Optional[str] = None) -> Dict[str, Any]:
        """Validate if user can like poll."""
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            return {
                "can_like": False,
                "reason": "Poll not found",
                "has_liked": False,
                "poll_active": False,
                "poll_exists": False
            }
        
        has_liked = self.get_user_like(db, poll_id, user_id, anon_id) is not None
        
        return {
            "can_like": poll.is_active and not has_liked,
            "reason": None if (poll.is_active and not has_liked) else (
                "Already liked" if has_liked else
                "Poll inactive"
            ),
            "has_liked": has_liked,
            "poll_active": poll.is_active,
            "poll_exists": True
        }
    
    def get_top_liked_polls(self, db: Session, skip: int = 0, limit: int = 20) -> List[Poll]:
        """Get top liked polls."""
        return db.query(Poll).filter(
            Poll.is_public == True,
            Poll.is_active == True
        ).order_by(desc(Poll.likes_count)).offset(skip).limit(limit).all()
    
    def get_recent_likes(self, db: Session, skip: int = 0, limit: int = 50) -> List[Like]:
        """Get recent likes across all polls."""
        return db.query(Like).order_by(desc(Like.created_at)).offset(skip).limit(limit).all()


# Create instance
like_crud = LikeCRUD()
