from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from app.models.vote import Vote
from app.models.poll import Poll
from app.models.option import Option
from app.schemas.vote import VoteCreate, MultipleVoteCreate, VoteUpdate
from app.utils.exceptions import PollNotFoundError, OptionNotFoundError, DuplicateVoteError, PollExpiredError, InvalidOptionError

logger = logging.getLogger(__name__)


class VoteCRUD:
    """CRUD operations for Vote model."""
    
    def create(self, db: Session, vote_data: VoteCreate, user_id: Optional[UUID] = None) -> Vote:
        """
        Create a new vote.
        
        Args:
            db: Database session
            vote_data: Vote creation data
            user_id: Optional user ID
            
        Returns:
            Vote: Created vote
            
        Raises:
            PollNotFoundError: If poll not found
            OptionNotFoundError: If option not found
            DuplicateVoteError: If user already voted
            PollExpiredError: If poll has expired
            InvalidOptionError: If option doesn't belong to poll
        """
        # Verify poll exists and is active
        poll = db.query(Poll).filter(Poll.id == vote_data.poll_id).first()
        if not poll:
            raise PollNotFoundError(str(vote_data.poll_id))
        
        if not poll.can_vote:
            if poll.is_expired:
                raise PollExpiredError(str(vote_data.poll_id))
            else:
                raise PollNotFoundError(str(vote_data.poll_id))
        
        # Verify option exists and belongs to poll
        option = db.query(Option).filter(
            and_(
                Option.id == vote_data.option_id,
                Option.poll_id == vote_data.poll_id
            )
        ).first()
        
        if not option:
            raise InvalidOptionError(str(vote_data.option_id), str(vote_data.poll_id))
        
        # Check for existing vote
        existing_vote = self.get_user_vote(db, vote_data.poll_id, user_id, vote_data.anon_id)
        if existing_vote:
            raise DuplicateVoteError(str(vote_data.poll_id))
        
        # Create vote
        db_vote = Vote(
            poll_id=vote_data.poll_id,
            option_id=vote_data.option_id,
            user_id=user_id,
            anon_id=vote_data.anon_id,
            ip_address=vote_data.ip_address,
            user_agent=vote_data.user_agent
        )
        
        db.add(db_vote)
        
        # Update option vote count
        option.increment_votes()
        
        # Update poll vote count
        poll.total_votes += 1
        
        db.commit()
        db.refresh(db_vote)
        
        logger.info(f"Vote created: {db_vote.id} for poll {vote_data.poll_id}")
        return db_vote
    
    def create_multiple(self, db: Session, vote_data: MultipleVoteCreate, user_id: Optional[UUID] = None) -> List[Vote]:
        """
        Create multiple votes for a poll.
        
        Args:
            db: Database session
            vote_data: Multiple vote creation data
            user_id: Optional user ID
            
        Returns:
            List[Vote]: Created votes
        """
        # Verify poll exists and allows multiple votes
        poll = db.query(Poll).filter(Poll.id == vote_data.poll_id).first()
        if not poll:
            raise PollNotFoundError(str(vote_data.poll_id))
        
        if not poll.can_vote:
            if poll.is_expired:
                raise PollExpiredError(str(vote_data.poll_id))
            else:
                raise PollNotFoundError(str(vote_data.poll_id))
        
        if not poll.allow_multiple:
            raise InvalidOptionError("Poll does not allow multiple votes", str(vote_data.poll_id))
        
        # Verify all options exist and belong to poll
        options = db.query(Option).filter(
            and_(
                Option.id.in_(vote_data.option_ids),
                Option.poll_id == vote_data.poll_id
            )
        ).all()
        
        if len(options) != len(vote_data.option_ids):
            raise InvalidOptionError("One or more options are invalid", str(vote_data.poll_id))
        
        # Check for existing votes
        existing_votes = self.get_user_votes(db, vote_data.poll_id, user_id, vote_data.anon_id)
        if existing_votes:
            raise DuplicateVoteError(str(vote_data.poll_id))
        
        # Create votes
        votes = []
        for option_id in vote_data.option_ids:
            db_vote = Vote(
                poll_id=vote_data.poll_id,
                option_id=option_id,
                user_id=user_id,
                anon_id=vote_data.anon_id,
                ip_address=vote_data.ip_address,
                user_agent=vote_data.user_agent
            )
            db.add(db_vote)
            votes.append(db_vote)
        
        # Update option vote counts
        for option in options:
            option.increment_votes()
        
        # Update poll vote count
        poll.total_votes += len(vote_data.option_ids)
        
        db.commit()
        
        for vote in votes:
            db.refresh(vote)
        
        logger.info(f"Multiple votes created: {len(votes)} votes for poll {vote_data.poll_id}")
        return votes
    
    def get(self, db: Session, vote_id: UUID) -> Optional[Vote]:
        """Get vote by ID."""
        return db.query(Vote).filter(Vote.id == vote_id).first()
    
    def get_user_vote(self, db: Session, poll_id: UUID, user_id: Optional[UUID] = None, 
                     anon_id: Optional[str] = None) -> Optional[Vote]:
        """Get user's vote for a poll."""
        query = db.query(Vote).filter(Vote.poll_id == poll_id)
        
        if user_id:
            query = query.filter(Vote.user_id == user_id)
        elif anon_id:
            query = query.filter(Vote.anon_id == anon_id)
        else:
            return None
        
        return query.first()
    
    def get_user_votes(self, db: Session, poll_id: UUID, user_id: Optional[UUID] = None, 
                      anon_id: Optional[str] = None) -> List[Vote]:
        """Get user's votes for a poll (for multiple choice polls)."""
        query = db.query(Vote).filter(Vote.poll_id == poll_id)
        
        if user_id:
            query = query.filter(Vote.user_id == user_id)
        elif anon_id:
            query = query.filter(Vote.anon_id == anon_id)
        else:
            return []
        
        return query.all()
    
    def get_by_poll(self, db: Session, poll_id: UUID, skip: int = 0, limit: int = 100) -> List[Vote]:
        """Get all votes for a poll."""
        return db.query(Vote).filter(Vote.poll_id == poll_id).offset(skip).limit(limit).all()
    
    def get_by_option(self, db: Session, option_id: UUID, skip: int = 0, limit: int = 100) -> List[Vote]:
        """Get all votes for an option."""
        return db.query(Vote).filter(Vote.option_id == option_id).offset(skip).limit(limit).all()
    
    def get_by_user(self, db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Vote]:
        """Get votes cast by a specific authenticated user."""
        return (
            db.query(Vote)
            .filter(Vote.user_id == user_id)
            .order_by(desc(Vote.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_with_details(self, db: Session, vote_id: UUID) -> Optional[Vote]:
        """Get vote with poll and option details."""
        return db.query(Vote).options(
            joinedload(Vote.poll),
            joinedload(Vote.option),
            joinedload(Vote.user)
        ).filter(Vote.id == vote_id).first()
    
    def update(self, db: Session, vote_id: UUID, vote_data: VoteUpdate) -> Optional[Vote]:
        """
        Update vote (change option).
        
        Args:
            db: Database session
            vote_id: Vote ID
            vote_data: Update data
            
        Returns:
            Vote: Updated vote or None if not found
        """
        db_vote = self.get_with_details(db, vote_id)
        if not db_vote:
            return None
        
        # Check if poll allows vote changes
        if not db_vote.poll.is_active or db_vote.poll.is_expired:
            raise PollNotFoundError(str(db_vote.poll_id))
        
        # Verify new option exists and belongs to poll
        new_option = db.query(Option).filter(
            and_(
                Option.id == vote_data.option_id,
                Option.poll_id == db_vote.poll_id
            )
        ).first()
        
        if not new_option:
            raise InvalidOptionError(str(vote_data.option_id), str(db_vote.poll_id))
        
        # Update vote counts
        old_option = db_vote.option
        old_option.decrement_votes()
        new_option.increment_votes()
        
        # Update vote
        db_vote.option_id = vote_data.option_id
        db.commit()
        db.refresh(db_vote)
        
        logger.info(f"Vote updated: {db_vote.id} for poll {db_vote.poll_id}")
        return db_vote
    
    def delete(self, db: Session, vote_id: UUID) -> bool:
        """
        Delete vote.
        
        Args:
            db: Database session
            vote_id: Vote ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        db_vote = self.get_with_details(db, vote_id)
        if not db_vote:
            return False
        
        # Update vote counts
        db_vote.option.decrement_votes()
        db_vote.poll.total_votes -= 1
        
        db.delete(db_vote)
        db.commit()
        
        logger.info(f"Vote deleted: {db_vote.id} for poll {db_vote.poll_id}")
        return True
    
    def get_stats(self, db: Session, poll_id: UUID) -> Dict[str, Any]:
        """Get vote statistics for a poll."""
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            raise PollNotFoundError(str(poll_id))
        
        votes = self.get_by_poll(db, poll_id)
        
        # Count votes by option
        votes_by_option = {}
        for vote in votes:
            option_id = str(vote.option_id)
            if option_id not in votes_by_option:
                votes_by_option[option_id] = 0
            votes_by_option[option_id] += 1
        
        # Count unique voters
        unique_voters = set()
        anonymous_votes = 0
        authenticated_votes = 0
        
        for vote in votes:
            if vote.user_id:
                unique_voters.add(str(vote.user_id))
                authenticated_votes += 1
            elif vote.anon_id:
                unique_voters.add(vote.anon_id)
                anonymous_votes += 1
        
        return {
            "poll_id": str(poll_id),
            "total_votes": len(votes),
            "unique_voters": len(unique_voters),
            "anonymous_votes": anonymous_votes,
            "authenticated_votes": authenticated_votes,
            "votes_by_option": votes_by_option,
            "poll_total_votes": poll.total_votes
        }
    
    def get_user_vote_history(self, db: Session, user_id: Optional[UUID] = None, 
                            anon_id: Optional[str] = None, skip: int = 0, limit: int = 50) -> List[Vote]:
        """Get user's vote history."""
        query = db.query(Vote)
        
        if user_id:
            query = query.filter(Vote.user_id == user_id)
        elif anon_id:
            query = query.filter(Vote.anon_id == anon_id)
        else:
            return []
        
        return query.order_by(desc(Vote.created_at)).offset(skip).limit(limit).all()
    
    def validate_vote_permission(self, db: Session, poll_id: UUID, user_id: Optional[UUID] = None, 
                               anon_id: Optional[str] = None) -> Dict[str, Any]:
        """Validate if user can vote on poll."""
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            return {
                "can_vote": False,
                "reason": "Poll not found",
                "has_voted": False,
                "poll_expired": False,
                "poll_active": False
            }
        
        has_voted = self.get_user_vote(db, poll_id, user_id, anon_id) is not None
        
        return {
            "can_vote": poll.can_vote and not has_voted,
            "reason": None if (poll.can_vote and not has_voted) else (
                "Already voted" if has_voted else
                "Poll expired" if poll.is_expired else
                "Poll inactive"
            ),
            "has_voted": has_voted,
            "poll_expired": poll.is_expired,
            "poll_active": poll.is_active
        }
    
    def get_multiple(self, db: Session, skip: int = 0, limit: int = 100, 
                    poll_id: Optional[UUID] = None, user_id: Optional[UUID] = None) -> List[Vote]:
        """Get multiple votes with optional filtering."""
        query = db.query(Vote)
        
        if poll_id:
            query = query.filter(Vote.poll_id == poll_id)
        if user_id:
            query = query.filter(Vote.user_id == user_id)
        
        return query.order_by(desc(Vote.created_at)).offset(skip).limit(limit).all()
    
    def count(self, db: Session, poll_id: Optional[UUID] = None, user_id: Optional[UUID] = None) -> int:
        """Count votes with optional filtering."""
        query = db.query(Vote)
        
        if poll_id:
            query = query.filter(Vote.poll_id == poll_id)
        if user_id:
            query = query.filter(Vote.user_id == user_id)
        
        return query.count()
    
    def count_by_poll(self, db: Session, poll_id: UUID) -> int:
        """Count votes for a specific poll."""
        return db.query(Vote).filter(Vote.poll_id == poll_id).count()
    
    def count_by_user(self, db: Session, user_id: UUID) -> int:
        """Count votes by a specific user."""
        return db.query(Vote).filter(Vote.user_id == user_id).count()
    
    def count_by_anonymous(self, db: Session, anon_id: str) -> int:
        """Count votes by an anonymous user."""
        return db.query(Vote).filter(Vote.anon_id == anon_id).count()
    
    def get_by_anonymous(self, db: Session, anon_id: str, skip: int = 0, limit: int = 100) -> List[Vote]:
        """Get votes by an anonymous user."""
        return db.query(Vote).filter(Vote.anon_id == anon_id).order_by(desc(Vote.created_at)).offset(skip).limit(limit).all()
    
    def get_by_liker(self, db: Session, poll_id: UUID, user_id: Optional[UUID] = None, 
                    anon_id: Optional[str] = None) -> Optional[Vote]:
        """Get vote by liker (alias for get_user_vote for consistency)."""
        return self.get_user_vote(db, poll_id, user_id, anon_id)


# Create instance
vote_crud = VoteCRUD()
