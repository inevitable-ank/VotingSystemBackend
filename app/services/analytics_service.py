from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
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

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for handling analytics and reporting."""
    
    def __init__(self):
        self.poll_crud = poll_crud
        self.vote_crud = vote_crud
        self.like_crud = like_crud
        self.user_crud = user_crud
    
    def get_poll_analytics(self, db: Session, poll_id: UUID) -> Dict[str, Any]:
        """Get comprehensive analytics for a specific poll."""
        try:
            poll = self.poll_crud.get_with_details(db, poll_id)
            if not poll:
                return {"error": "Poll not found"}
            
            # Basic poll stats
            poll_stats = {
                "poll_id": str(poll_id),
                "title": poll.title,
                "created_at": poll.created_at.isoformat(),
                "total_votes": poll.total_votes,
                "total_likes": poll.likes_count,
                "views_count": poll.views_count,
                "is_active": poll.is_active,
                "is_expired": poll.is_expired
            }
            
            # Vote analytics
            vote_stats = self.vote_crud.get_stats(db, poll_id)
            
            # Like analytics
            like_stats = self.like_crud.get_stats(db, poll_id)
            
            # Option breakdown
            options_breakdown = []
            for option in poll.options:
                percentage = (option.vote_count / poll.total_votes * 100) if poll.total_votes > 0 else 0
                options_breakdown.append({
                    "option_id": str(option.id),
                    "text": option.text,
                    "position": option.position,
                    "vote_count": option.vote_count,
                    "percentage": round(percentage, 2)
                })
            
            # Time-based analytics
            time_analytics = self._get_time_based_analytics(db, poll_id)
            
            # Engagement metrics
            engagement_metrics = self._calculate_engagement_metrics(db, poll_id)
            
            return {
                "poll_stats": poll_stats,
                "vote_stats": vote_stats,
                "like_stats": like_stats,
                "options_breakdown": options_breakdown,
                "time_analytics": time_analytics,
                "engagement_metrics": engagement_metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting poll analytics: {e}")
            return {"error": "Failed to get poll analytics"}
    
    def get_user_analytics(self, db: Session, user_id: UUID) -> Dict[str, Any]:
        """Get analytics for a specific user."""
        try:
            user = self.user_crud.get(db, user_id)
            if not user:
                return {"error": "User not found"}
            
            # User stats
            user_stats = {
                "user_id": str(user_id),
                "username": user.username,
                "created_at": user.created_at.isoformat(),
                "is_active": user.is_active,
                "is_verified": user.is_verified
            }
            
            # Poll creation stats
            polls_created = self.poll_crud.get_by_author(db, user_id)
            poll_stats = {
                "total_polls": len(polls_created),
                "active_polls": len([p for p in polls_created if p.is_active]),
                "expired_polls": len([p for p in polls_created if p.is_expired]),
                "total_votes_received": sum(p.total_votes for p in polls_created),
                "total_likes_received": sum(p.likes_count for p in polls_created),
                "total_views_received": sum(p.views_count for p in polls_created)
            }
            
            # Voting stats
            user_votes = self.vote_crud.get_by_user(db, user_id)
            voting_stats = {
                "total_votes_cast": len(user_votes),
                "polls_voted_on": len(set(v.poll_id for v in user_votes)),
                "recent_votes": len([v for v in user_votes if v.created_at > datetime.now() - timedelta(days=7)])
            }
            
            # Liking stats
            user_likes = self.like_crud.get_by_user(db, user_id)
            liking_stats = {
                "total_likes_given": len(user_likes),
                "polls_liked": len(set(l.poll_id for l in user_likes)),
                "recent_likes": len([l for l in user_likes if l.created_at > datetime.now() - timedelta(days=7)])
            }
            
            return {
                "user_stats": user_stats,
                "poll_stats": poll_stats,
                "voting_stats": voting_stats,
                "liking_stats": liking_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
            return {"error": "Failed to get user analytics"}
    
    def get_platform_analytics(self, db: Session) -> Dict[str, Any]:
        """Get platform-wide analytics."""
        try:
            # Overall stats
            total_polls = db.query(Poll).count()
            active_polls = db.query(Poll).filter(Poll.is_active == True).count()
            expired_polls = db.query(Poll).filter(Poll.expires_at < func.now()).count()
            
            total_votes = db.query(func.sum(Poll.total_votes)).scalar() or 0
            total_likes = db.query(func.sum(Poll.likes_count)).scalar() or 0
            total_views = db.query(func.sum(Poll.views_count)).scalar() or 0
            
            total_users = db.query(User).count()
            active_users = db.query(User).filter(User.is_active == True).count()
            
            # Recent activity
            recent_polls = db.query(Poll).filter(
                Poll.created_at > datetime.now() - timedelta(days=7)
            ).count()
            
            recent_votes = db.query(Vote).filter(
                Vote.created_at > datetime.now() - timedelta(days=7)
            ).count()
            
            recent_likes = db.query(Like).filter(
                Like.created_at > datetime.now() - timedelta(days=7)
            ).count()
            
            # Top polls
            top_polls = db.query(Poll).filter(
                Poll.is_public == True
            ).order_by(desc(Poll.total_votes)).limit(10).all()
            
            top_polls_data = []
            for poll in top_polls:
                top_polls_data.append({
                    "poll_id": str(poll.id),
                    "title": poll.title,
                    "total_votes": poll.total_votes,
                    "likes_count": poll.likes_count,
                    "views_count": poll.views_count,
                    "created_at": poll.created_at.isoformat()
                })
            
            # Growth metrics
            growth_metrics = self._calculate_growth_metrics(db)
            
            return {
                "overall_stats": {
                    "total_polls": total_polls,
                    "active_polls": active_polls,
                    "expired_polls": expired_polls,
                    "total_votes": total_votes,
                    "total_likes": total_likes,
                    "total_views": total_views,
                    "total_users": total_users,
                    "active_users": active_users
                },
                "recent_activity": {
                    "polls_created_week": recent_polls,
                    "votes_cast_week": recent_votes,
                    "likes_given_week": recent_likes
                },
                "top_polls": top_polls_data,
                "growth_metrics": growth_metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting platform analytics: {e}")
            return {"error": "Failed to get platform analytics"}
    
    def _get_time_based_analytics(self, db: Session, poll_id: UUID) -> Dict[str, Any]:
        """Get time-based analytics for a poll."""
        try:
            # Votes over time (last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            votes_over_time = db.query(
                func.date(Vote.created_at).label('date'),
                func.count(Vote.id).label('count')
            ).filter(
                Vote.poll_id == poll_id,
                Vote.created_at >= thirty_days_ago
            ).group_by(func.date(Vote.created_at)).all()
            
            # Likes over time (last 30 days)
            likes_over_time = db.query(
                func.date(Like.created_at).label('date'),
                func.count(Like.id).label('count')
            ).filter(
                Like.poll_id == poll_id,
                Like.created_at >= thirty_days_ago
            ).group_by(func.date(Like.created_at)).all()
            
            return {
                "votes_over_time": [{"date": str(v.date), "count": v.count} for v in votes_over_time],
                "likes_over_time": [{"date": str(l.date), "count": l.count} for l in likes_over_time]
            }
            
        except Exception as e:
            logger.error(f"Error getting time-based analytics: {e}")
            return {"votes_over_time": [], "likes_over_time": []}
    
    def _calculate_engagement_metrics(self, db: Session, poll_id: UUID) -> Dict[str, Any]:
        """Calculate engagement metrics for a poll."""
        try:
            poll = self.poll_crud.get(db, poll_id)
            if not poll:
                return {}
            
            # Calculate engagement rate
            total_interactions = poll.total_votes + poll.likes_count
            engagement_rate = (total_interactions / poll.views_count * 100) if poll.views_count > 0 else 0
            
            # Calculate vote-to-view ratio
            vote_to_view_ratio = (poll.total_votes / poll.views_count * 100) if poll.views_count > 0 else 0
            
            # Calculate like-to-view ratio
            like_to_view_ratio = (poll.likes_count / poll.views_count * 100) if poll.views_count > 0 else 0
            
            return {
                "engagement_rate": round(engagement_rate, 2),
                "vote_to_view_ratio": round(vote_to_view_ratio, 2),
                "like_to_view_ratio": round(like_to_view_ratio, 2),
                "total_interactions": total_interactions
            }
            
        except Exception as e:
            logger.error(f"Error calculating engagement metrics: {e}")
            return {}
    
    def _calculate_growth_metrics(self, db: Session) -> Dict[str, Any]:
        """Calculate growth metrics for the platform."""
        try:
            # Users created this week vs last week
            this_week = datetime.now() - timedelta(days=7)
            last_week = datetime.now() - timedelta(days=14)
            
            users_this_week = db.query(User).filter(User.created_at >= this_week).count()
            users_last_week = db.query(User).filter(
                and_(User.created_at >= last_week, User.created_at < this_week)
            ).count()
            
            user_growth = ((users_this_week - users_last_week) / users_last_week * 100) if users_last_week > 0 else 0
            
            # Polls created this week vs last week
            polls_this_week = db.query(Poll).filter(Poll.created_at >= this_week).count()
            polls_last_week = db.query(Poll).filter(
                and_(Poll.created_at >= last_week, Poll.created_at < this_week)
            ).count()
            
            poll_growth = ((polls_this_week - polls_last_week) / polls_last_week * 100) if polls_last_week > 0 else 0
            
            return {
                "user_growth_percentage": round(user_growth, 2),
                "poll_growth_percentage": round(poll_growth, 2),
                "users_this_week": users_this_week,
                "users_last_week": users_last_week,
                "polls_this_week": polls_this_week,
                "polls_last_week": polls_last_week
            }
            
        except Exception as e:
            logger.error(f"Error calculating growth metrics: {e}")
            return {}
    
    def get_trending_polls(self, db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        """Get trending polls based on recent activity."""
        try:
            # Get polls with high engagement in the last 7 days
            seven_days_ago = datetime.now() - timedelta(days=7)
            
            trending_polls = db.query(Poll).filter(
                and_(
                    Poll.is_public == True,
                    Poll.is_active == True,
                    Poll.created_at >= seven_days_ago
                )
            ).order_by(
                desc(Poll.total_votes + Poll.likes_count),
                desc(Poll.views_count)
            ).limit(limit).all()
            
            trending_data = []
            for poll in trending_polls:
                trending_data.append({
                    "poll_id": str(poll.id),
                    "title": poll.title,
                    "slug": poll.slug,
                    "total_votes": poll.total_votes,
                    "likes_count": poll.likes_count,
                    "views_count": poll.views_count,
                    "created_at": poll.created_at.isoformat(),
                    "trend_score": poll.total_votes + poll.likes_count + poll.views_count
                })
            
            return trending_data
            
        except Exception as e:
            logger.error(f"Error getting trending polls: {e}")
            return []
    
    def export_poll_data(self, db: Session, poll_id: UUID) -> Dict[str, Any]:
        """Export comprehensive data for a poll."""
        try:
            poll = self.poll_crud.get_with_details(db, poll_id)
            if not poll:
                return {"error": "Poll not found"}
            
            # Get all votes
            votes = self.vote_crud.get_by_poll(db, poll_id)
            votes_data = []
            for vote in votes:
                votes_data.append({
                    "vote_id": str(vote.id),
                    "option_id": str(vote.option_id),
                    "user_id": str(vote.user_id) if vote.user_id else None,
                    "anon_id": vote.anon_id,
                    "ip_address": vote.ip_address,
                    "created_at": vote.created_at.isoformat()
                })
            
            # Get all likes
            likes = self.like_crud.get_by_poll(db, poll_id)
            likes_data = []
            for like in likes:
                likes_data.append({
                    "like_id": str(like.id),
                    "user_id": str(like.user_id) if like.user_id else None,
                    "anon_id": like.anon_id,
                    "ip_address": like.ip_address,
                    "created_at": like.created_at.isoformat()
                })
            
            return {
                "poll": {
                    "id": str(poll.id),
                    "title": poll.title,
                    "description": poll.description,
                    "slug": poll.slug,
                    "author_id": str(poll.author_id) if poll.author_id else None,
                    "is_active": poll.is_active,
                    "allow_multiple": poll.allow_multiple,
                    "is_public": poll.is_public,
                    "expires_at": poll.expires_at.isoformat() if poll.expires_at else None,
                    "created_at": poll.created_at.isoformat(),
                    "updated_at": poll.updated_at.isoformat(),
                    "total_votes": poll.total_votes,
                    "likes_count": poll.likes_count,
                    "views_count": poll.views_count
                },
                "options": [
                    {
                        "id": str(option.id),
                        "text": option.text,
                        "position": option.position,
                        "vote_count": option.vote_count
                    }
                    for option in poll.options
                ],
                "votes": votes_data,
                "likes": likes_data,
                "exported_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error exporting poll data: {e}")
            return {"error": "Failed to export poll data"}


# Create instance
analytics_service = AnalyticsService()
