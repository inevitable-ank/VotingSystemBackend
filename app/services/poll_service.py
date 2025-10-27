from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
import logging

from app.models.poll import Poll
from app.models.vote import Vote
from app.models.like import Like
from app.models.user import User
from app.crud.poll import poll_crud
from app.crud.vote import vote_crud
from app.crud.like import like_crud
from app.crud.user import user_crud
from app.schemas.poll import PollCreate, PollUpdate
from app.services.analytics_service import analytics_service
from app.services.notification_service import notification_service
from app.services.websocket_service import websocket_service

logger = logging.getLogger(__name__)


class PollService:
    """Service for handling poll business logic."""
    
    def __init__(self):
        self.poll_crud = poll_crud
        self.vote_crud = vote_crud
        self.like_crud = like_crud
        self.user_crud = user_crud
        self.analytics_service = analytics_service
        self.notification_service = notification_service
        self.websocket_service = websocket_service
    
    def create_poll(self, db: Session, poll_data: PollCreate, author_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Create a new poll with business logic."""
        try:
            # Create poll
            poll = self.poll_crud.create(db, poll_data, author_id)
            
            # Send notification
            self.notification_service.send_poll_created_notification(db, poll.id)
            
            # Send WebSocket notification
            poll_data_dict = {
                "id": str(poll.id),
                "title": poll.title,
                "slug": poll.slug,
                "author_id": str(poll.author_id) if poll.author_id else None,
                "created_at": poll.created_at.isoformat()
            }
            
            # Note: WebSocket broadcast would be handled in the route
            # await self.websocket_service.handle_poll_created(str(poll.id), poll_data_dict, manager)
            
            return {
                "success": True,
                "poll": poll,
                "message": "Poll created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating poll: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create poll"
            }
    
    def get_poll_with_analytics(self, db: Session, poll_id: UUID) -> Dict[str, Any]:
        """Get poll with analytics data."""
        try:
            poll = self.poll_crud.get_with_details(db, poll_id)
            if not poll:
                return {
                    "success": False,
                    "error": "Poll not found",
                    "message": "Poll not found"
                }
            
            # Get analytics
            analytics = self.analytics_service.get_poll_analytics(db, poll_id)
            
            return {
                "success": True,
                "poll": poll,
                "analytics": analytics,
                "message": "Poll retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Error getting poll with analytics: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get poll"
            }
    
    def cast_vote(self, db: Session, poll_id: UUID, option_ids: List[UUID], 
                  user_id: Optional[UUID] = None, anon_id: Optional[str] = None,
                  ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Dict[str, Any]:
        """Cast vote with business logic."""
        try:
            # Validate poll exists and is active
            poll = self.poll_crud.get_with_options(db, poll_id)
            if not poll:
                return {
                    "success": False,
                    "error": "Poll not found",
                    "message": "Poll not found"
                }
            
            if not poll.can_vote:
                return {
                    "success": False,
                    "error": "Poll not active",
                    "message": "Poll is not active or has expired"
                }
            
            # Check if user has already voted (for single-choice polls)
            if not poll.allow_multiple:
                existing_vote = self.vote_crud.get_user_vote(db, poll_id, user_id, anon_id)
                if existing_vote:
                    return {
                        "success": False,
                        "error": "Already voted",
                        "message": "You have already voted on this poll"
                    }
            
            # Create vote(s)
            if len(option_ids) == 1:
                # Single vote
                vote_data = {
                    "poll_id": poll_id,
                    "option_id": option_ids[0],
                    "anon_id": anon_id,
                    "ip_address": ip_address,
                    "user_agent": user_agent
                }
                vote = self.vote_crud.create(db, vote_data, user_id)
                votes = [vote]
            else:
                # Multiple votes
                vote_data = {
                    "poll_id": poll_id,
                    "option_ids": option_ids,
                    "anon_id": anon_id,
                    "ip_address": ip_address,
                    "user_agent": user_agent
                }
                votes = self.vote_crud.create_multiple(db, vote_data, user_id)
            
            # Update poll vote counts
            self.poll_crud.update_vote_counts(db, poll_id)
            
            # Send notification
            self.notification_service.send_vote_cast_notification(db, poll_id, user_id)
            
            # Send WebSocket notification
            vote_data_dict = {
                "poll_id": str(poll_id),
                "option_ids": [str(oid) for oid in option_ids],
                "user_id": str(user_id) if user_id else None,
                "anon_id": anon_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Note: WebSocket broadcast would be handled in the route
            # await self.websocket_service.handle_vote_cast(str(poll_id), vote_data_dict, manager)
            
            return {
                "success": True,
                "votes": votes,
                "message": "Vote cast successfully"
            }
            
        except Exception as e:
            logger.error(f"Error casting vote: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to cast vote"
            }
    
    def like_poll(self, db: Session, poll_id: UUID, user_id: Optional[UUID] = None,
                  anon_id: Optional[str] = None, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Like poll with business logic."""
        try:
            # Validate poll exists
            poll = self.poll_crud.get(db, poll_id)
            if not poll:
                return {
                    "success": False,
                    "error": "Poll not found",
                    "message": "Poll not found"
                }
            
            # Check if user has already liked
            existing_like = self.like_crud.get_user_like(db, poll_id, user_id, anon_id)
            if existing_like:
                return {
                    "success": False,
                    "error": "Already liked",
                    "message": "You have already liked this poll"
                }
            
            # Create like
            like_data = {
                "poll_id": poll_id,
                "anon_id": anon_id,
                "ip_address": ip_address
            }
            like = self.like_crud.create(db, like_data, user_id)
            
            # Update poll likes count
            self.poll_crud.update_likes_count(db, poll_id)
            
            # Send notification
            self.notification_service.send_like_notification(db, poll_id, user_id)
            
            # Send WebSocket notification
            like_data_dict = {
                "poll_id": str(poll_id),
                "user_id": str(user_id) if user_id else None,
                "anon_id": anon_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Note: WebSocket broadcast would be handled in the route
            # await self.websocket_service.handle_like_cast(str(poll_id), like_data_dict, manager)
            
            return {
                "success": True,
                "like": like,
                "message": "Poll liked successfully"
            }
            
        except Exception as e:
            logger.error(f"Error liking poll: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to like poll"
            }
    
    def unlike_poll(self, db: Session, poll_id: UUID, user_id: Optional[UUID] = None,
                    anon_id: Optional[str] = None) -> Dict[str, Any]:
        """Unlike poll with business logic."""
        try:
            # Validate poll exists
            poll = self.poll_crud.get(db, poll_id)
            if not poll:
                return {
                    "success": False,
                    "error": "Poll not found",
                    "message": "Poll not found"
                }
            
            # Check if user has liked
            existing_like = self.like_crud.get_user_like(db, poll_id, user_id, anon_id)
            if not existing_like:
                return {
                    "success": False,
                    "error": "Not liked",
                    "message": "You have not liked this poll"
                }
            
            # Delete like
            success = self.like_crud.delete_user_like(db, poll_id, user_id, anon_id)
            if not success:
                return {
                    "success": False,
                    "error": "Failed to unlike",
                    "message": "Failed to unlike poll"
                }
            
            # Update poll likes count
            self.poll_crud.update_likes_count(db, poll_id)
            
            return {
                "success": True,
                "message": "Poll unliked successfully"
            }
            
        except Exception as e:
            logger.error(f"Error unliking poll: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to unlike poll"
            }
    
    def get_trending_polls(self, db: Session, limit: int = 20) -> Dict[str, Any]:
        """Get trending polls with business logic."""
        try:
            # Get trending polls from analytics service
            trending_polls = self.analytics_service.get_trending_polls(db, limit)
            
            return {
                "success": True,
                "polls": trending_polls,
                "message": "Trending polls retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Error getting trending polls: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get trending polls"
            }
    
    def get_user_polls_with_stats(self, db: Session, user_id: UUID, skip: int = 0, limit: int = 20) -> Dict[str, Any]:
        """Get user's polls with statistics."""
        try:
            # Get user's polls
            polls = self.poll_crud.get_by_author(db, user_id, skip, limit)
            
            # Get user analytics
            user_analytics = self.analytics_service.get_user_analytics(db, user_id)
            
            # Format polls with additional stats
            polls_data = []
            for poll in polls:
                poll_dict = {
                    "id": str(poll.id),
                    "title": poll.title,
                    "slug": poll.slug,
                    "description": poll.description,
                    "is_active": poll.is_active,
                    "is_public": poll.is_public,
                    "expires_at": poll.expires_at.isoformat() if poll.expires_at else None,
                    "created_at": poll.created_at.isoformat(),
                    "total_votes": poll.total_votes,
                    "likes_count": poll.likes_count,
                    "views_count": poll.views_count,
                    "can_vote": poll.can_vote,
                    "is_expired": poll.is_expired
                }
                polls_data.append(poll_dict)
            
            return {
                "success": True,
                "polls": polls_data,
                "analytics": user_analytics,
                "message": "User polls retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Error getting user polls with stats: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get user polls"
            }
    
    def update_poll(self, db: Session, poll_id: UUID, poll_data: PollUpdate, user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Update poll with business logic."""
        try:
            # Check if poll exists
            poll = self.poll_crud.get(db, poll_id)
            if not poll:
                return {
                    "success": False,
                    "error": "Poll not found",
                    "message": "Poll not found"
                }
            
            # Check authorization
            if user_id and poll.author_id != user_id:
                return {
                    "success": False,
                    "error": "Unauthorized",
                    "message": "You can only update your own polls"
                }
            
            # Update poll
            updated_poll = self.poll_crud.update(db, poll_id, poll_data)
            if not updated_poll:
                return {
                    "success": False,
                    "error": "Update failed",
                    "message": "Failed to update poll"
                }
            
            # Send WebSocket notification
            poll_data_dict = {
                "id": str(updated_poll.id),
                "title": updated_poll.title,
                "slug": updated_poll.slug,
                "updated_at": updated_poll.updated_at.isoformat()
            }
            
            # Note: WebSocket broadcast would be handled in the route
            # await self.websocket_service.handle_poll_updated(str(poll_id), poll_data_dict, manager)
            
            return {
                "success": True,
                "poll": updated_poll,
                "message": "Poll updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error updating poll: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update poll"
            }
    
    def delete_poll(self, db: Session, poll_id: UUID, user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Delete poll with business logic."""
        try:
            # Check if poll exists
            poll = self.poll_crud.get(db, poll_id)
            if not poll:
                return {
                    "success": False,
                    "error": "Poll not found",
                    "message": "Poll not found"
                }
            
            # Check authorization
            if user_id and poll.author_id != user_id:
                return {
                    "success": False,
                    "error": "Unauthorized",
                    "message": "You can only delete your own polls"
                }
            
            # Delete poll
            success = self.poll_crud.delete(db, poll_id)
            if not success:
                return {
                    "success": False,
                    "error": "Delete failed",
                    "message": "Failed to delete poll"
                }
            
            # Send WebSocket notification
            # Note: WebSocket broadcast would be handled in the route
            # await self.websocket_service.handle_poll_deleted(str(poll_id), manager)
            
            return {
                "success": True,
                "message": "Poll deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting poll: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to delete poll"
            }
    
    def check_poll_expiration(self, db: Session) -> Dict[str, Any]:
        """Check for expired polls and handle them."""
        try:
            # Get expired polls
            expired_polls = self.poll_crud.get_expired(db)
            
            results = {
                "expired_polls": len(expired_polls),
                "notifications_sent": 0,
                "errors": []
            }
            
            for poll in expired_polls:
                try:
                    # Send expiration notification
                    self.notification_service.send_poll_expired_notification(db, poll.id)
                    results["notifications_sent"] += 1
                    
                    # Send WebSocket notification
                    poll_data_dict = {
                        "id": str(poll.id),
                        "title": poll.title,
                        "expires_at": poll.expires_at.isoformat() if poll.expires_at else None
                    }
                    
                    # Note: WebSocket broadcast would be handled in the route
                    # await self.websocket_service.handle_poll_expired(str(poll.id), poll_data_dict, manager)
                    
                except Exception as e:
                    results["errors"].append(f"Poll {poll.id}: {str(e)}")
            
            return {
                "success": True,
                "results": results,
                "message": "Poll expiration check completed"
            }
            
        except Exception as e:
            logger.error(f"Error checking poll expiration: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to check poll expiration"
            }
    
    def get_poll_recommendations(self, db: Session, user_id: Optional[UUID] = None, limit: int = 10) -> Dict[str, Any]:
        """Get poll recommendations for a user."""
        try:
            # Simple recommendation logic - get popular active polls
            recommended_polls = self.poll_crud.get_popular(db, limit=limit)
            
            # Filter out polls user has already voted on
            if user_id:
                user_votes = self.vote_crud.get_by_user(db, user_id)
                voted_poll_ids = {vote.poll_id for vote in user_votes}
                recommended_polls = [p for p in recommended_polls if p.id not in voted_poll_ids]
            
            # Format recommendations
            recommendations = []
            for poll in recommended_polls:
                recommendations.append({
                    "id": str(poll.id),
                    "title": poll.title,
                    "slug": poll.slug,
                    "description": poll.description,
                    "total_votes": poll.total_votes,
                    "likes_count": poll.likes_count,
                    "views_count": poll.views_count,
                    "created_at": poll.created_at.isoformat(),
                    "reason": "Popular poll"
                })
            
            return {
                "success": True,
                "recommendations": recommendations,
                "message": "Poll recommendations retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Error getting poll recommendations: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get poll recommendations"
            }


# Create instance
poll_service = PollService()
