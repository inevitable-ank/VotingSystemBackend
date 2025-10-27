from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set, Optional
import json
import logging
from uuid import UUID
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time features."""
    
    def __init__(self):
        # Store active connections by poll_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store connections by user_id for user-specific updates
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        # Store global connections
        self.global_connections: Set[WebSocket] = set()
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, poll_id: Optional[str] = None, user_id: Optional[str] = None):
        """Accept a WebSocket connection."""
        await websocket.accept()
        
        # Store connection metadata
        self.connection_metadata[websocket] = {
            "poll_id": poll_id,
            "user_id": user_id,
            "connected_at": datetime.now(),
            "last_ping": datetime.now()
        }
        
        if poll_id:
            if poll_id not in self.active_connections:
                self.active_connections[poll_id] = set()
            self.active_connections[poll_id].add(websocket)
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
        
        # Add to global connections
        self.global_connections.add(websocket)
        
        logger.info(f"WebSocket connected: poll_id={poll_id}, user_id={user_id}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        metadata = self.connection_metadata.get(websocket, {})
        poll_id = metadata.get("poll_id")
        user_id = metadata.get("user_id")
        
        if poll_id and poll_id in self.active_connections:
            self.active_connections[poll_id].discard(websocket)
            if not self.active_connections[poll_id]:
                del self.active_connections[poll_id]
        
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Remove from global connections
        self.global_connections.discard(websocket)
        
        # Remove metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
        
        logger.info(f"WebSocket disconnected: poll_id={poll_id}, user_id={user_id}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast_to_poll(self, message: str, poll_id: str):
        """Broadcast a message to all connections for a specific poll."""
        if poll_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[poll_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to poll {poll_id}: {e}")
                    disconnected.add(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.disconnect(connection)
    
    async def broadcast_to_user(self, message: str, user_id: str):
        """Broadcast a message to all connections for a specific user."""
        if user_id in self.user_connections:
            disconnected = set()
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {e}")
                    disconnected.add(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.disconnect(connection)
    
    async def broadcast_to_all(self, message: str):
        """Broadcast a message to all active connections."""
        disconnected = set()
        for connection in self.global_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to all: {e}")
                disconnected.add(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_poll_update(self, poll_id: str, update_type: str, data: dict):
        """Send poll update to relevant connections."""
        message = {
            "type": "poll_update",
            "poll_id": poll_id,
            "update_type": update_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_poll(json.dumps(message), poll_id)
        await self.broadcast_to_all(json.dumps(message))
    
    async def send_vote_update(self, poll_id: str, vote_data: dict):
        """Send vote update to relevant connections."""
        message = {
            "type": "vote_cast",
            "poll_id": poll_id,
            "data": vote_data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_poll(json.dumps(message), poll_id)
        await self.broadcast_to_all(json.dumps(message))
    
    async def send_like_update(self, poll_id: str, like_data: dict):
        """Send like update to relevant connections."""
        message = {
            "type": "like_cast",
            "poll_id": poll_id,
            "data": like_data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_poll(json.dumps(message), poll_id)
        await self.broadcast_to_all(json.dumps(message))
    
    async def send_user_notification(self, user_id: str, notification: dict):
        """Send notification to a specific user."""
        message = {
            "type": "notification",
            "data": notification,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_user(json.dumps(message), user_id)
    
    async def send_system_announcement(self, announcement: dict):
        """Send system announcement to all connections."""
        message = {
            "type": "system_announcement",
            "data": announcement,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_all(json.dumps(message))
    
    async def handle_heartbeat(self, websocket: WebSocket):
        """Handle heartbeat ping from client."""
        try:
            # Update last ping time
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["last_ping"] = datetime.now()
            
            # Send pong response
            pong_message = {
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }
            await self.send_personal_message(json.dumps(pong_message), websocket)
            
        except Exception as e:
            logger.error(f"Error handling heartbeat: {e}")
            self.disconnect(websocket)
    
    def get_connection_stats(self) -> dict:
        """Get connection statistics."""
        return {
            "total_connections": len(self.global_connections),
            "poll_connections": len(self.active_connections),
            "user_connections": len(self.user_connections),
            "connections_by_poll": {poll_id: len(connections) for poll_id, connections in self.active_connections.items()},
            "connections_by_user": {user_id: len(connections) for user_id, connections in self.user_connections.items()}
        }
    
    def get_connection_info(self, websocket: WebSocket) -> Optional[dict]:
        """Get information about a specific connection."""
        return self.connection_metadata.get(websocket)
    
    def cleanup_stale_connections(self):
        """Clean up stale connections (connections that haven't pinged recently)."""
        stale_threshold = datetime.now() - timedelta(minutes=5)
        stale_connections = []
        
        for websocket, metadata in self.connection_metadata.items():
            last_ping = metadata.get("last_ping", datetime.now())
            if last_ping < stale_threshold:
                stale_connections.append(websocket)
        
        for websocket in stale_connections:
            logger.info("Cleaning up stale WebSocket connection")
            self.disconnect(websocket)
    
    async def handle_client_message(self, websocket: WebSocket, message: str):
        """Handle incoming message from client."""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "ping":
                await self.handle_heartbeat(websocket)
            elif message_type == "subscribe":
                # Handle subscription to specific channels
                await self.handle_subscription(websocket, data)
            elif message_type == "unsubscribe":
                # Handle unsubscription
                await self.handle_unsubscription(websocket, data)
            else:
                # Unknown message type
                error_message = {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                    "timestamp": datetime.now().isoformat()
                }
                await self.send_personal_message(json.dumps(error_message), websocket)
                
        except json.JSONDecodeError:
            error_message = {
                "type": "error",
                "message": "Invalid JSON format",
                "timestamp": datetime.now().isoformat()
            }
            await self.send_personal_message(json.dumps(error_message), websocket)
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
            error_message = {
                "type": "error",
                "message": "Internal server error",
                "timestamp": datetime.now().isoformat()
            }
            await self.send_personal_message(json.dumps(error_message), websocket)
    
    async def handle_subscription(self, websocket: WebSocket, data: dict):
        """Handle client subscription to channels."""
        try:
            poll_id = data.get("poll_id")
            user_id = data.get("user_id")
            
            if poll_id:
                if poll_id not in self.active_connections:
                    self.active_connections[poll_id] = set()
                self.active_connections[poll_id].add(websocket)
                
                # Update metadata
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]["poll_id"] = poll_id
            
            if user_id:
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = set()
                self.user_connections[user_id].add(websocket)
                
                # Update metadata
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]["user_id"] = user_id
            
            # Send confirmation
            confirmation = {
                "type": "subscribed",
                "data": {
                    "poll_id": poll_id,
                    "user_id": user_id,
                    "message": "Successfully subscribed"
                },
                "timestamp": datetime.now().isoformat()
            }
            await self.send_personal_message(json.dumps(confirmation), websocket)
            
        except Exception as e:
            logger.error(f"Error handling subscription: {e}")
    
    async def handle_unsubscription(self, websocket: WebSocket, data: dict):
        """Handle client unsubscription from channels."""
        try:
            poll_id = data.get("poll_id")
            user_id = data.get("user_id")
            
            if poll_id and poll_id in self.active_connections:
                self.active_connections[poll_id].discard(websocket)
                if not self.active_connections[poll_id]:
                    del self.active_connections[poll_id]
            
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(websocket)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Send confirmation
            confirmation = {
                "type": "unsubscribed",
                "data": {
                    "poll_id": poll_id,
                    "user_id": user_id,
                    "message": "Successfully unsubscribed"
                },
                "timestamp": datetime.now().isoformat()
            }
            await self.send_personal_message(json.dumps(confirmation), websocket)
            
        except Exception as e:
            logger.error(f"Error handling unsubscription: {e}")


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
