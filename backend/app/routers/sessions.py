from fastapi import APIRouter, Depends, HTTPException, status
from app.auth import get_current_user
from app.db.sessions import create_voting_session, update_voting_session, get_active_session, get_context_ids, get_session_context
from app.db.crud import ensure_user_sync
from app.db.permissions import check_permission
from app.models.domain import Role, VotingSession
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.services.connection_manager import manager
import json

router = APIRouter(prefix="/sessions", tags=["sessions"])

class CreateSessionRequest(BaseModel):
    theme_version_id: str
    config: Dict[str, Any] = {"dots_per_user": 3, "time_limit": None}

class UpdateSessionRequest(BaseModel):
    status: str

@router.post("/")
async def start_session(data: CreateSessionRequest, user: dict = Depends(get_current_user)):
    user_email = user.get("email")
    
    # Resolve Context
    theme_id, project_id = await get_context_ids(data.theme_version_id)
    if not theme_id:
        raise HTTPException(status_code=404, detail="Theme Version context not found")

    # Check Permissions on Theme (Moderator+)
    is_allowed = await check_permission(user.get("id"), theme_id, Role.MODERATOR)
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Not authorized to start voting session")

    # Sync User to Graph (Ensure they exist for relationship creation)
    user_id = user.get("id")
    await ensure_user_sync(user_id, user_email, user.get("user_metadata", {}).get("full_name"))

    try:
        # Create Session
        session_id, _ = await create_voting_session(data.theme_version_id, user.get("id"), data.config)
        
        # Broadcast
        if project_id:
            await manager.broadcast_data(project_id, {
                "type": "SESSION_STARTED",
                "payload": {
                    "session_id": session_id,
                    "theme_version_id": data.theme_version_id,
                    "config": data.config,
                    "status": "active"
                }
            })
        
        return {"id": session_id, "status": "active"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{session_id}")
async def update_session(session_id: str, data: UpdateSessionRequest, user: dict = Depends(get_current_user)):
    user_email = user.get("email")
    
    # Resolve Context from session
    theme_id, project_id = await get_session_context(session_id)
    if not theme_id:
        raise HTTPException(status_code=404, detail="Session context not found")
        
    # Check Permissions (Moderator+)
    is_allowed = await check_permission(user.get("id"), theme_id, Role.MODERATOR)
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Not authorized to update voting session")

    # Update
    updated_project_id = await update_voting_session(session_id, data.status)
    
    # Broadcast
    if project_id: # Use context project_id
        await manager.broadcast_data(project_id, {
            "type": "SESSION_UPDATED",
            "payload": {
                "session_id": session_id,
                "status": data.status
            }
        })
        
    return {"status": data.status}

@router.get("/active")
async def get_active_session_endpoint(theme_version_id: str, user: dict = Depends(get_current_user)):
    # Read permission? VIEWER/MEMBER on Theme.
    theme_id, _ = await get_context_ids(theme_version_id)
    if not theme_id:
        raise HTTPException(status_code=404, detail="Theme Version context not found")
        
    user_email = user.get("email")
    can_view = await check_permission(user.get("id"), theme_id, Role.VIEWER)
    if not can_view:
        raise HTTPException(status_code=403, detail="Not authorized to view sessions")

    session = await get_active_session(theme_version_id)
    return session
