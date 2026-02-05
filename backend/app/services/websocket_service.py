"""
WorkSynapse WebSocket Service
=============================
Service layer for WebSocket operations including:
- Connection management
- Message broadcasting
- Room/channel management
"""

from typing import Dict, List, Optional, Set
from fastapi import WebSocket
import logging
import json

logger = logging.getLogger(__name__)


class WebSocketService:
    """
    WebSocket service for real-time communication.
    
    Provides:
    - Connection tracking
    - Room-based messaging
    - Broadcast capabilities
    """
    
    def __init__(self):
        # Active connections: {user_id: [websockets]}
        self.active_connections: Dict[int, List[WebSocket]] = {}
        
        # Room memberships: {room_id: set of user_ids}
        self.rooms: Dict[str, Set[int]] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
    ) -> None:
        """
        Register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected: user={user_id}")
    
    def disconnect(
        self,
        websocket: WebSocket,
        user_id: int,
    ) -> None:
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # Remove from all rooms
        for room_users in self.rooms.values():
            room_users.discard(user_id)
        
        logger.info(f"WebSocket disconnected: user={user_id}")
    
    async def send_personal(
        self,
        message: dict,
        user_id: int,
    ) -> None:
        """
        Send a message to a specific user.
        
        Args:
            message: Message dict to send
            user_id: Target user ID
        """
        if user_id in self.active_connections:
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
    
    async def broadcast(
        self,
        message: dict,
        exclude_user: Optional[int] = None,
    ) -> None:
        """
        Broadcast a message to all connected users.
        
        Args:
            message: Message dict to send
            exclude_user: User ID to exclude from broadcast
        """
        for user_id, sockets in self.active_connections.items():
            if exclude_user and user_id == exclude_user:
                continue
            
            for websocket in sockets:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {e}")
    
    async def join_room(
        self,
        user_id: int,
        room_id: str,
    ) -> None:
        """
        Add a user to a room.
        
        Args:
            user_id: User ID
            room_id: Room identifier
        """
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        
        self.rooms[room_id].add(user_id)
        logger.debug(f"User {user_id} joined room {room_id}")
    
    async def leave_room(
        self,
        user_id: int,
        room_id: str,
    ) -> None:
        """
        Remove a user from a room.
        
        Args:
            user_id: User ID
            room_id: Room identifier
        """
        if room_id in self.rooms:
            self.rooms[room_id].discard(user_id)
            
            # Clean up empty rooms
            if not self.rooms[room_id]:
                del self.rooms[room_id]
        
        logger.debug(f"User {user_id} left room {room_id}")
    
    async def send_to_room(
        self,
        message: dict,
        room_id: str,
        exclude_user: Optional[int] = None,
    ) -> None:
        """
        Send a message to all users in a room.
        
        Args:
            message: Message dict to send
            room_id: Target room
            exclude_user: User ID to exclude
        """
        if room_id not in self.rooms:
            return
        
        for user_id in self.rooms[room_id]:
            if exclude_user and user_id == exclude_user:
                continue
            
            await self.send_personal(message, user_id)
    
    def get_room_users(self, room_id: str) -> Set[int]:
        """
        Get all users in a room.
        
        Args:
            room_id: Room identifier
            
        Returns:
            Set of user IDs
        """
        return self.rooms.get(room_id, set())
    
    def get_online_users(self) -> List[int]:
        """
        Get all online user IDs.
        
        Returns:
            List of user IDs
        """
        return list(self.active_connections.keys())
    
    def is_user_online(self, user_id: int) -> bool:
        """
        Check if a user is online.
        
        Args:
            user_id: User ID
            
        Returns:
            True if user has active connections
        """
        return user_id in self.active_connections


# Singleton instance
websocket_service = WebSocketService()
