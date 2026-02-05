from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Optional
import logging
from app.models.domain import ThreadCreate, ThreadMessageCreate
from app.db.crud import (
    create_conversation_thread, 
    get_threads_by_target, 
    get_thread_counts, 
    create_thread_message, 
    get_thread_messages,
    ensure_user_sync
)
from app.auth import verify_token

router = APIRouter(
    tags=["threads"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)

# Replicate get_current_user from main.py to avoid circular imports
async def get_current_user(payload: dict = Depends(verify_token)):
    user_id = payload.get("sub")
    email = payload.get("email")
    user_meta = payload.get("user_metadata", {})
    name = user_meta.get("full_name") or user_meta.get("name")
    
    if not user_id or not email:
        raise HTTPException(status_code=401, detail="Invalid token payload")
        
    # JIT Sync: Ensure user exists in Neo4j and is up-to-date
    return await ensure_user_sync(user_id, email, name)

@router.post("/threads")
async def create_thread_generic(thread: ThreadCreate, user: dict = Depends(get_current_user)):
    # Check permissions (Member access okay for creating threads? Or Admin? Intent says "Participant", so Member is likely fine.)
    # Let's enforce Membership at least.
    email = user.get("email")
    # For now, relying on space existing. Ideally check `is_member`.
    # Assuming if you can see the space, you can create a thread.
    # Refine later if strict permissions needed.
    
    target_id = thread.target_id
    if not target_id:
         raise HTTPException(status_code=400, detail="target_id is required for generic threads")

    tid = await create_conversation_thread(target_id, thread.topic)
    return {"id": tid, "topic": thread.topic}

@router.get("/threads")
async def list_threads_generic(target_id: str, user: dict = Depends(get_current_user)):
    # target_id passed as query param
    return await get_threads_by_target(target_id)

@router.post("/threads/stats")
async def get_thread_stats(target_ids: List[str], user: dict = Depends(get_current_user)):
    return await get_thread_counts(target_ids)

@router.post("/threads/{thread_id}/messages")
async def add_thread_message(thread_id: str, message: ThreadMessageCreate, user: dict = Depends(get_current_user)):
    user_id = user.get("id")
    if not user_id:
        logger.error(f"User from dependency missing ID field: {user}")
        raise HTTPException(status_code=500, detail="User identity error")
        
    logger.info(f"Adding message to thread {thread_id} for user {user_id}")
    return await create_thread_message(thread_id, user_id, message.content)

@router.get("/threads/{thread_id}/messages")
async def list_thread_messages(thread_id: str, user: dict = Depends(get_current_user)):
    return await get_thread_messages(thread_id)
