from typing import Dict, List, Any, Optional, Set
from uuid import UUID
from datetime import datetime
import json
import logging
import asyncio

logger = logging.getLogger(__name__)


class WebSocketService:
    """Service for handling WebSocket communications."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set] = {}
        self.user_connections: Dict[str, Set] = {}
        self.poll_connections: Dict[str, Set] = {}
        self.global_connections: Set = set()
    
    def get_timestamp(self) -> str:
        """Get current timestamp."""
        return datetime.now().isoformat()
    
    async def handle_vote_cast(self, poll_id: str, vote_data: Dict[str, Any], manager) -> None:
        """Handle vote cast WebSocket message."""
        try:
            message = {
                "type": "vote_cast",
                "poll_id": poll_id,
                "data": vote_data,
                "timestamp": self.get_timestamp()
            }
            
            # Broadcast to poll-specific connections
            await manager.broadcast_to_poll(json.dumps(message), poll_id)
            
            # Broadcast to global connections
            await manager.broadcast_to_all(json.dumps(message))
            
            logger.info(f"Vote cast WebSocket message sent for poll {poll_id}")
            
        except Exception as e:
            logger.error(f"Error handling vote cast WebSocket message: {e}")
    
    async def handle_like_cast(self, poll_id: str, like_data: Dict[str, Any], manager) -> None:
        """Handle like cast WebSocket message."""
        try:
            message = {
                "type": "like_cast",
                "poll_id": poll_id,
                "data": like_data,
                "timestamp": self.get_timestamp()
            }
            
            # Broadcast to poll-specific connections
            await manager.broadcast_to_poll(json.dumps(message), poll_id)
            
            # Broadcast to global connections
            await manager.broadcast_to_all(json.dumps(message))
            
            logger.info(f"Like cast WebSocket message sent for poll {poll_id}")
            
        except Exception as e:
            logger.error(f"Error handling like cast WebSocket message: {e}")
    
    async def handle_poll_created(self, poll_id: str, poll_data: Dict[str, Any], manager) -> None:
        """Handle poll created WebSocket message."""
        try:
            message = {
                "type": "poll_created",
                "poll_id": poll_id,
                "data": poll_data,
                "timestamp": self.get_timestamp()
            }
            
            # Broadcast to global connections
            await manager.broadcast_to_all(json.dumps(message))
            
            logger.info(f"Poll created WebSocket message sent for poll {poll_id}")
            
        except Exception as e:
            logger.error(f"Error handling poll created WebSocket message: {e}")
    
    async def handle_poll_updated(self, poll_id: str, poll_data: Dict[str, Any], manager) -> None:
        """Handle poll updated WebSocket message."""
        try:
            message = {
                "type": "poll_updated",
                "poll_id": poll_id,
                "data": poll_data,
                "timestamp": self.get_timestamp()
            }
            
            # Broadcast to poll-specific connections
            await manager.broadcast_to_poll(json.dumps(message), poll_id)
            
            # Broadcast to global connections
            await manager.broadcast_to_all(json.dumps(message))
            
            logger.info(f"Poll updated WebSocket message sent for poll {poll_id}")
            
        except Exception as e:
            logger.error(f"Error handling poll updated WebSocket message: {e}")
    
    async def handle_poll_deleted(self, poll_id: str, manager) -> None:
        """Handle poll deleted WebSocket message."""
        try:
            message = {
                "type": "poll_deleted",
                "poll_id": poll_id,
                "timestamp": self.get_timestamp()
            }
            
            # Broadcast to poll-specific connections
            await manager.broadcast_to_poll(json.dumps(message), poll_id)
            
            # Broadcast to global connections
            await manager.broadcast_to_all(json.dumps(message))
            
            logger.info(f"Poll deleted WebSocket message sent for poll {poll_id}")
            
        except Exception as e:
            logger.error(f"Error handling poll deleted WebSocket message: {e}")
    
    async def handle_poll_expired(self, poll_id: str, poll_data: Dict[str, Any], manager) -> None:
        """Handle poll expired WebSocket message."""
        try:
            message = {
                "type": "poll_expired",
                "poll_id": poll_id,
                "data": poll_data,
                "timestamp": self.get_timestamp()
            }
            
            # Broadcast to poll-specific connections
            await manager.broadcast_to_poll(json.dumps(message), poll_id)
            
            # Broadcast to global connections
            await manager.broadcast_to_all(json.dumps(message))
            
            logger.info(f"Poll expired WebSocket message sent for poll {poll_id}")
            
        except Exception as e:
            logger.error(f"Error handling poll expired WebSocket message: {e}")
    
    async def handle_user_activity(self, user_id: str, activity_data: Dict[str, Any], manager) -> None:
        """Handle user activity WebSocket message."""
        try:
            message = {
                "type": "user_activity",
                "user_id": user_id,
                "data": activity_data,
                "timestamp": self.get_timestamp()
            }
            
            # Broadcast to user-specific connections
            await manager.broadcast_to_user(json.dumps(message), user_id)
            
            logger.info(f"User activity WebSocket message sent for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling user activity WebSocket message: {e}")
    
    async def handle_system_notification(self, notification_data: Dict[str, Any], manager) -> None:
        """Handle system notification WebSocket message."""
        try:
            message = {
                "type": "system_notification",
                "data": notification_data,
                "timestamp": self.get_timestamp()
            }
            
            # Broadcast to all connections
            await manager.broadcast_to_all(json.dumps(message))
            
            logger.info("System notification WebSocket message sent")
            
        except Exception as e:
            logger.error(f"Error handling system notification WebSocket message: {e}")
    
    async def handle_poll_analytics_update(self, poll_id: str, analytics_data: Dict[str, Any], manager) -> None:
        """Handle poll analytics update WebSocket message."""
        try:
            message = {
                "type": "poll_analytics_update",
                "poll_id": poll_id,
                "data": analytics_data,
                "timestamp": self.get_timestamp()
            }
            
            # Broadcast to poll-specific connections
            await manager.broadcast_to_poll(json.dumps(message), poll_id)
            
            logger.info(f"Poll analytics update WebSocket message sent for poll {poll_id}")
            
        except Exception as e:
            logger.error(f"Error handling poll analytics update WebSocket message: {e}")
    
    async def handle_real_time_stats(self, stats_data: Dict[str, Any], manager) -> None:
        """Handle real-time stats WebSocket message."""
        try:
            message = {
                "type": "real_time_stats",
                "data": stats_data,
                "timestamp": self.get_timestamp()
            }
            
            # Broadcast to global connections
            await manager.broadcast_to_all(json.dumps(message))
            
            logger.info("Real-time stats WebSocket message sent")
            
        except Exception as e:
            logger.error(f"Error handling real-time stats WebSocket message: {e}")
    
    async def handle_connection_status(self, connection_id: str, status: str, manager) -> None:
        """Handle connection status WebSocket message."""
        try:
            message = {
                "type": "connection_status",
                "connection_id": connection_id,
                "status": status,
                "timestamp": self.get_timestamp()
            }
            
            # Broadcast to global connections
            await manager.broadcast_to_all(json.dumps(message))
            
            logger.info(f"Connection status WebSocket message sent: {connection_id} - {status}")
            
        except Exception as e:
            logger.error(f"Error handling connection status WebSocket message: {e}")
    
    async def handle_heartbeat(self, manager) -> None:
        """Handle heartbeat WebSocket message."""
        try:
            message = {
                "type": "heartbeat",
                "timestamp": self.get_timestamp(),
                "active_connections": len(manager.active_connections),
                "user_connections": len(manager.user_connections),
                "global_connections": len(manager.global_connections)
            }
            
            # Broadcast to all connections
            await manager.broadcast_to_all(json.dumps(message))
            
            logger.debug("Heartbeat WebSocket message sent")
            
        except Exception as e:
            logger.error(f"Error handling heartbeat WebSocket message: {e}")
    
    async def handle_error(self, error_data: Dict[str, Any], manager) -> None:
        """Handle error WebSocket message."""
        try:
            message = {
                "type": "error",
                "data": error_data,
                "timestamp": self.get_timestamp()
            }
            
            # Broadcast to all connections
            await manager.broadcast_to_all(json.dumps(message))
            
            logger.error(f"Error WebSocket message sent: {error_data}")
            
        except Exception as e:
            logger.error(f"Error handling error WebSocket message: {e}")
    
    async def handle_custom_message(self, message_type: str, data: Dict[str, Any], manager, target: Optional[str] = None) -> None:
        """Handle custom WebSocket message."""
        try:
            message = {
                "type": message_type,
                "data": data,
                "timestamp": self.get_timestamp()
            }
            
            if target:
                # Send to specific target (poll, user, etc.)
                if target.startswith("poll_"):
                    await manager.broadcast_to_poll(json.dumps(message), target)
                elif target.startswith("user_"):
                    await manager.broadcast_to_user(json.dumps(message), target)
                else:
                    await manager.broadcast_to_all(json.dumps(message))
            else:
                # Broadcast to all connections
                await manager.broadcast_to_all(json.dumps(message))
            
            logger.info(f"Custom WebSocket message sent: {message_type}")
            
        except Exception as e:
            logger.error(f"Error handling custom WebSocket message: {e}")
    
    def validate_message(self, message: Dict[str, Any]) -> bool:
        """Validate WebSocket message format."""
        try:
            required_fields = ["type", "timestamp"]
            
            for field in required_fields:
                if field not in message:
                    return False
            
            # Validate message type
            valid_types = [
                "ping", "pong", "subscribe", "vote_cast", "like_cast",
                "poll_created", "poll_updated", "poll_deleted", "poll_expired",
                "user_activity", "system_notification", "poll_analytics_update",
                "real_time_stats", "connection_status", "heartbeat", "error"
            ]
            
            if message["type"] not in valid_types:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating WebSocket message: {e}")
            return False
    
    def format_message(self, message_type: str, data: Dict[str, Any], target: Optional[str] = None) -> Dict[str, Any]:
        """Format WebSocket message."""
        try:
            message = {
                "type": message_type,
                "data": data,
                "timestamp": self.get_timestamp()
            }
            
            if target:
                message["target"] = target
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting WebSocket message: {e}")
            return {
                "type": "error",
                "data": {"error": "Failed to format message"},
                "timestamp": self.get_timestamp()
            }
    
    def get_connection_stats(self, manager) -> Dict[str, Any]:
        """Get WebSocket connection statistics."""
        try:
            return {
                "active_connections": len(manager.active_connections),
                "user_connections": len(manager.user_connections),
                "global_connections": len(manager.global_connections),
                "total_connections": len(manager.active_connections) + len(manager.user_connections) + len(manager.global_connections),
                "timestamp": self.get_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error getting connection stats: {e}")
            return {
                "active_connections": 0,
                "user_connections": 0,
                "global_connections": 0,
                "total_connections": 0,
                "timestamp": self.get_timestamp()
            }


# Create instance
websocket_service = WebSocketService()

