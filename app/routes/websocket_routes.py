from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List, Set
import json
import logging
from uuid import UUID

from app.services.websocket_service import websocket_service
from app.utils.exceptions import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        # Store active connections by poll_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store connections by user_id for user-specific updates
        self.user_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, poll_id: str = None, user_id: str = None):
        """Accept a WebSocket connection."""
        await websocket.accept()
        
        if poll_id:
            if poll_id not in self.active_connections:
                self.active_connections[poll_id] = set()
            self.active_connections[poll_id].add(websocket)
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
        
        logger.info(f"WebSocket connected: poll_id={poll_id}, user_id={user_id}")
    
    def disconnect(self, websocket: WebSocket, poll_id: str = None, user_id: str = None):
        """Remove a WebSocket connection."""
        if poll_id and poll_id in self.active_connections:
            self.active_connections[poll_id].discard(websocket)
            if not self.active_connections[poll_id]:
                del self.active_connections[poll_id]
        
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        logger.info(f"WebSocket disconnected: poll_id={poll_id}, user_id={user_id}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
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
                self.active_connections[poll_id].discard(connection)
    
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
                self.user_connections[user_id].discard(connection)
    
    async def broadcast_to_all(self, message: str):
        """Broadcast a message to all active connections."""
        all_connections = set()
        
        # Collect all connections
        for connections in self.active_connections.values():
            all_connections.update(connections)
        for connections in self.user_connections.values():
            all_connections.update(connections)
        
        # Send to all connections
        disconnected = set()
        for connection in all_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to all: {e}")
                disconnected.add(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            for connections in self.active_connections.values():
                connections.discard(connection)
            for connections in self.user_connections.values():
                connections.discard(connection)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/poll/{poll_id}")
async def websocket_poll_endpoint(websocket: WebSocket, poll_id: str):
    """WebSocket endpoint for poll-specific updates."""
    await manager.connect(websocket, poll_id=poll_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    # Respond to ping with pong
                    await manager.send_personal_message(
                        json.dumps({"type": "pong", "timestamp": message.get("timestamp")}),
                        websocket
                    )
                elif message_type == "subscribe":
                    # Client wants to subscribe to poll updates
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "subscribed",
                            "poll_id": poll_id,
                            "message": "Successfully subscribed to poll updates"
                        }),
                        websocket
                    )
                elif message_type == "vote_cast":
                    # Handle vote cast notification
                    await websocket_service.handle_vote_cast(
                        poll_id=poll_id,
                        vote_data=message.get("data", {}),
                        manager=manager
                    )
                elif message_type == "like_cast":
                    # Handle like cast notification
                    await websocket_service.handle_like_cast(
                        poll_id=poll_id,
                        like_data=message.get("data", {}),
                        manager=manager
                    )
                else:
                    # Unknown message type
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "error",
                            "message": f"Unknown message type: {message_type}"
                        }),
                        websocket
                    )
                    
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }),
                    websocket
                )
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Internal server error"
                    }),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, poll_id=poll_id)
        logger.info(f"WebSocket disconnected from poll {poll_id}")


@router.websocket("/user/{user_id}")
async def websocket_user_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for user-specific updates."""
    await manager.connect(websocket, user_id=user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    # Respond to ping with pong
                    await manager.send_personal_message(
                        json.dumps({"type": "pong", "timestamp": message.get("timestamp")}),
                        websocket
                    )
                elif message_type == "subscribe":
                    # Client wants to subscribe to user updates
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "subscribed",
                            "user_id": user_id,
                            "message": "Successfully subscribed to user updates"
                        }),
                        websocket
                    )
                else:
                    # Unknown message type
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "error",
                            "message": f"Unknown message type: {message_type}"
                        }),
                        websocket
                    )
                    
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }),
                    websocket
                )
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Internal server error"
                    }),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id=user_id)
        logger.info(f"WebSocket disconnected from user {user_id}")


@router.websocket("/global")
async def websocket_global_endpoint(websocket: WebSocket):
    """WebSocket endpoint for global updates."""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    # Respond to ping with pong
                    await manager.send_personal_message(
                        json.dumps({"type": "pong", "timestamp": message.get("timestamp")}),
                        websocket
                    )
                elif message_type == "subscribe":
                    # Client wants to subscribe to global updates
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "subscribed",
                            "message": "Successfully subscribed to global updates"
                        }),
                        websocket
                    )
                else:
                    # Unknown message type
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "error",
                            "message": f"Unknown message type: {message_type}"
                        }),
                        websocket
                    )
                    
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }),
                    websocket
                )
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Internal server error"
                    }),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket disconnected from global endpoint")


# WebSocket service functions
async def broadcast_poll_update(poll_id: str, update_type: str, data: dict):
    """Broadcast poll update to all connected clients."""
    message = {
        "type": "poll_update",
        "poll_id": poll_id,
        "update_type": update_type,
        "data": data,
        "timestamp": websocket_service.get_timestamp()
    }
    
    await manager.broadcast_to_poll(json.dumps(message), poll_id)


async def broadcast_user_update(user_id: str, update_type: str, data: dict):
    """Broadcast user update to all connected clients."""
    message = {
        "type": "user_update",
        "user_id": user_id,
        "update_type": update_type,
        "data": data,
        "timestamp": websocket_service.get_timestamp()
    }
    
    await manager.broadcast_to_user(json.dumps(message), user_id)


async def broadcast_global_update(update_type: str, data: dict):
    """Broadcast global update to all connected clients."""
    message = {
        "type": "global_update",
        "update_type": update_type,
        "data": data,
        "timestamp": websocket_service.get_timestamp()
    }
    
    await manager.broadcast_to_all(json.dumps(message))
