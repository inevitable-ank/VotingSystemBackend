from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

from app.models.poll import Poll
from app.models.user import User
from app.models.vote import Vote
from app.models.like import Like
from app.crud.poll import poll_crud
from app.crud.user import user_crud
from app.crud.vote import vote_crud
from app.crud.like import like_crud

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for handling notifications and communications."""
    
    def __init__(self):
        self.poll_crud = poll_crud
        self.user_crud = user_crud
        self.vote_crud = vote_crud
        self.like_crud = like_crud
        
        # Email configuration (would be loaded from environment variables)
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email_username = None  # Would be loaded from config
        self.email_password = None  # Would be loaded from config
    
    def send_poll_created_notification(self, db: Session, poll_id: UUID) -> bool:
        """Send notification when a poll is created."""
        try:
            poll = self.poll_crud.get_with_details(db, poll_id)
            if not poll or not poll.author:
                return False
            
            # For now, just log the notification
            logger.info(f"Poll created notification: {poll.title} by {poll.author.username}")
            
            # In a real implementation, you would:
            # 1. Send email to poll author
            # 2. Send push notification if user has mobile app
            # 3. Send in-app notification
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending poll created notification: {e}")
            return False
    
    def send_vote_cast_notification(self, db: Session, poll_id: UUID, voter_id: Optional[UUID] = None) -> bool:
        """Send notification when a vote is cast."""
        try:
            poll = self.poll_crud.get_with_details(db, poll_id)
            if not poll:
                return False
            
            # Notify poll author if they have notifications enabled
            if poll.author and poll.author.is_active:
                logger.info(f"Vote cast notification: Vote on {poll.title} by {poll.author.username}")
                
                # In a real implementation, you would:
                # 1. Check user notification preferences
                # 2. Send email if enabled
                # 3. Send push notification if enabled
                # 4. Send in-app notification
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending vote cast notification: {e}")
            return False
    
    def send_like_notification(self, db: Session, poll_id: UUID, liker_id: Optional[UUID] = None) -> bool:
        """Send notification when a poll is liked."""
        try:
            poll = self.poll_crud.get_with_details(db, poll_id)
            if not poll:
                return False
            
            # Notify poll author if they have notifications enabled
            if poll.author and poll.author.is_active:
                logger.info(f"Like notification: {poll.title} liked by user")
                
                # In a real implementation, you would:
                # 1. Check user notification preferences
                # 2. Send email if enabled
                # 3. Send push notification if enabled
                # 4. Send in-app notification
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending like notification: {e}")
            return False
    
    def send_poll_expired_notification(self, db: Session, poll_id: UUID) -> bool:
        """Send notification when a poll expires."""
        try:
            poll = self.poll_crud.get_with_details(db, poll_id)
            if not poll or not poll.author:
                return False
            
            logger.info(f"Poll expired notification: {poll.title} by {poll.author.username}")
            
            # In a real implementation, you would:
            # 1. Send email with poll results
            # 2. Send push notification
            # 3. Send in-app notification with analytics
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending poll expired notification: {e}")
            return False
    
    def send_daily_summary(self, db: Session, user_id: UUID) -> bool:
        """Send daily summary to a user."""
        try:
            user = self.user_crud.get(db, user_id)
            if not user or not user.email:
                return False
            
            # Get user's activity for the day
            today = datetime.now().date()
            
            # Get polls created today
            polls_created = db.query(Poll).filter(
                Poll.author_id == user_id,
                Poll.created_at >= today
            ).count()
            
            # Get votes cast today
            votes_cast = db.query(Vote).filter(
                Vote.user_id == user_id,
                Vote.created_at >= today
            ).count()
            
            # Get likes given today
            likes_given = db.query(Like).filter(
                Like.user_id == user_id,
                Like.created_at >= today
            ).count()
            
            # Get votes received on user's polls today
            votes_received = db.query(Vote).join(Poll).filter(
                Poll.author_id == user_id,
                Vote.created_at >= today
            ).count()
            
            # Get likes received on user's polls today
            likes_received = db.query(Like).join(Poll).filter(
                Poll.author_id == user_id,
                Like.created_at >= today
            ).count()
            
            summary_data = {
                "user": user.username,
                "date": today.isoformat(),
                "activity": {
                    "polls_created": polls_created,
                    "votes_cast": votes_cast,
                    "likes_given": likes_given,
                    "votes_received": votes_received,
                    "likes_received": likes_received
                }
            }
            
            logger.info(f"Daily summary for {user.username}: {summary_data}")
            
            # In a real implementation, you would:
            # 1. Generate HTML email template
            # 2. Send email with summary
            # 3. Include poll analytics and insights
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
            return False
    
    def send_weekly_report(self, db: Session, user_id: UUID) -> bool:
        """Send weekly report to a user."""
        try:
            user = self.user_crud.get(db, user_id)
            if not user or not user.email:
                return False
            
            # Get user's activity for the week
            week_ago = datetime.now() - timedelta(days=7)
            
            # Get polls created this week
            polls_created = db.query(Poll).filter(
                Poll.author_id == user_id,
                Poll.created_at >= week_ago
            ).all()
            
            # Get votes cast this week
            votes_cast = db.query(Vote).filter(
                Vote.user_id == user_id,
                Vote.created_at >= week_ago
            ).all()
            
            # Get likes given this week
            likes_given = db.query(Like).filter(
                Like.user_id == user_id,
                Like.created_at >= week_ago
            ).all()
            
            # Calculate engagement metrics
            total_votes_received = sum(poll.total_votes for poll in polls_created)
            total_likes_received = sum(poll.likes_count for poll in polls_created)
            total_views_received = sum(poll.views_count for poll in polls_created)
            
            report_data = {
                "user": user.username,
                "week_start": week_ago.date().isoformat(),
                "week_end": datetime.now().date().isoformat(),
                "activity": {
                    "polls_created": len(polls_created),
                    "votes_cast": len(votes_cast),
                    "likes_given": len(likes_given),
                    "votes_received": total_votes_received,
                    "likes_received": total_likes_received,
                    "views_received": total_views_received
                },
                "top_polls": [
                    {
                        "title": poll.title,
                        "votes": poll.total_votes,
                        "likes": poll.likes_count,
                        "views": poll.views_count
                    }
                    for poll in sorted(polls_created, key=lambda p: p.total_votes, reverse=True)[:5]
                ]
            }
            
            logger.info(f"Weekly report for {user.username}: {report_data}")
            
            # In a real implementation, you would:
            # 1. Generate comprehensive HTML email
            # 2. Include charts and analytics
            # 3. Send email with insights and recommendations
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending weekly report: {e}")
            return False
    
    def send_poll_reminder(self, db: Session, poll_id: UUID) -> bool:
        """Send reminder about an active poll."""
        try:
            poll = self.poll_crud.get_with_details(db, poll_id)
            if not poll or not poll.author:
                return False
            
            # Check if poll is still active and has low engagement
            if not poll.is_active or poll.total_votes > 10:  # Don't remind if already popular
                return False
            
            logger.info(f"Poll reminder: {poll.title} by {poll.author.username}")
            
            # In a real implementation, you would:
            # 1. Send email to poll author
            # 2. Suggest ways to increase engagement
            # 3. Include sharing suggestions
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending poll reminder: {e}")
            return False
    
    def send_engagement_alert(self, db: Session, poll_id: UUID) -> bool:
        """Send alert when a poll gets high engagement."""
        try:
            poll = self.poll_crud.get_with_details(db, poll_id)
            if not poll or not poll.author:
                return False
            
            # Check if poll has high engagement
            if poll.total_votes < 50:  # Threshold for high engagement
                return False
            
            logger.info(f"Engagement alert: {poll.title} has {poll.total_votes} votes")
            
            # In a real implementation, you would:
            # 1. Send congratulatory email to poll author
            # 2. Include analytics and insights
            # 3. Suggest ways to capitalize on popularity
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending engagement alert: {e}")
            return False
    
    def send_system_notification(self, db: Session, user_id: UUID, message: str, notification_type: str = "info") -> bool:
        """Send system notification to a user."""
        try:
            user = self.user_crud.get(db, user_id)
            if not user:
                return False
            
            notification_data = {
                "user_id": str(user_id),
                "message": message,
                "type": notification_type,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"System notification for {user.username}: {message}")
            
            # In a real implementation, you would:
            # 1. Store notification in database
            # 2. Send push notification
            # 3. Send in-app notification
            # 4. Send email if critical
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending system notification: {e}")
            return False
    
    def send_bulk_notification(self, db: Session, user_ids: List[UUID], message: str, notification_type: str = "info") -> Dict[str, Any]:
        """Send bulk notification to multiple users."""
        try:
            results = {
                "sent": 0,
                "failed": 0,
                "errors": []
            }
            
            for user_id in user_ids:
                try:
                    success = self.send_system_notification(db, user_id, message, notification_type)
                    if success:
                        results["sent"] += 1
                    else:
                        results["failed"] += 1
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"User {user_id}: {str(e)}")
            
            logger.info(f"Bulk notification sent: {results['sent']} successful, {results['failed']} failed")
            
            return results
            
        except Exception as e:
            logger.error(f"Error sending bulk notification: {e}")
            return {"sent": 0, "failed": len(user_ids), "errors": [str(e)]}
    
    def _send_email(self, to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """Send email notification."""
        try:
            if not self.email_username or not self.email_password:
                logger.warning("Email credentials not configured")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_username, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_username, to_email, text)
            server.quit()
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False
    
    def _generate_email_template(self, template_type: str, data: Dict[str, Any]) -> str:
        """Generate email template."""
        try:
            if template_type == "poll_created":
                return f"""
                <h2>Poll Created Successfully!</h2>
                <p>Your poll "{data.get('title', '')}" has been created and is now live.</p>
                <p><a href="{data.get('poll_url', '#')}">View Poll</a></p>
                """
            
            elif template_type == "vote_cast":
                return f"""
                <h2>New Vote on Your Poll!</h2>
                <p>Someone just voted on your poll "{data.get('title', '')}".</p>
                <p><a href="{data.get('poll_url', '#')}">View Results</a></p>
                """
            
            elif template_type == "daily_summary":
                return f"""
                <h2>Daily Activity Summary</h2>
                <p>Here's what happened with your polls today:</p>
                <ul>
                    <li>Polls created: {data.get('polls_created', 0)}</li>
                    <li>Votes cast: {data.get('votes_cast', 0)}</li>
                    <li>Likes given: {data.get('likes_given', 0)}</li>
                    <li>Votes received: {data.get('votes_received', 0)}</li>
                    <li>Likes received: {data.get('likes_received', 0)}</li>
                </ul>
                """
            
            else:
                return f"<p>{data.get('message', 'Notification')}</p>"
                
        except Exception as e:
            logger.error(f"Error generating email template: {e}")
            return "<p>Notification</p>"


# Create instance
notification_service = NotificationService()

