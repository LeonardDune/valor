import logging
from typing import Dict, List, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Manages WebSocket connections partitioned by project_id.
    Handles broadcasting of both persistent data updates and ephemeral presence events.
    """
    def __init__(self):
        # active_connections: {project_id: {user_id: [WebSocket, ...]}}
        # We allow multiple connections per user (e.g. multiple tabs)
        self.active_connections: Dict[str, Dict[str, List[WebSocket]]] = {}

    async def connect(self, websocket: WebSocket, project_id: str, user_id: str):
        await websocket.accept()
        
        if project_id not in self.active_connections:
            self.active_connections[project_id] = {}
        
        if user_id not in self.active_connections[project_id]:
            self.active_connections[project_id][user_id] = []
            
        self.active_connections[project_id][user_id].append(websocket)
        logger.info(f"User {user_id} connected to project {project_id}")
        
        # Notify others that this user joined (Presence)
        await self.broadcast_presence(project_id, user_id, {"type": "USER_JOINED", "user_id": user_id})

    def disconnect(self, websocket: WebSocket, project_id: str, user_id: str):
        if project_id in self.active_connections:
            if user_id in self.active_connections[project_id]:
                try:
                    self.active_connections[project_id][user_id].remove(websocket)
                    if not self.active_connections[project_id][user_id]:
                        del self.active_connections[project_id][user_id]
                        # Notify others that this user left (Presence)
                        # Note: This is synchronous disconnect, we can't await here easily without creating a task
                        # For MVP we might skip generic 'left' or rely on heartbeat timeout on frontend
                        pass
                except ValueError:
                    pass
            
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]
        
        logger.info(f"User {user_id} disconnected from project {project_id}")

    async def broadcast_data(self, project_id: str, message: dict):
        """
        Broadcast persistent data updates (Graph mutations) to all connected clients in the project.
        """
        if project_id in self.active_connections:
            for user_connections in self.active_connections[project_id].values():
                for connection in user_connections:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting data: {e}")

    async def broadcast_presence(self, project_id: str, sender_id: str, message: dict):
        """
        Broadcast ephemeral presence events (Cursor, Focus) to all clients in the project EXCEPT the sender.
        """
        if project_id in self.active_connections:
            for user_id, connections in self.active_connections[project_id].items():
                if user_id == sender_id:
                    continue # Don't echo back to sender
                
                for connection in connections:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting presence: {e}")

# Global instance
manager = ConnectionManager()
