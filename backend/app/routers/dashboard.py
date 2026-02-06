from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import logging
from app.db.dashboard import get_user_environments
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    responses={404: {"description": "Not found"}},
)

@router.get("/environments")
async def get_my_environments(user: dict = Depends(get_current_user)):
    """
    Returns a hierarchical list of Organization -> Project -> Theme
    that the current user has access to.
    """
    try:
        email = user.get("email")
        if not email:
             raise HTTPException(status_code=401, detail="User not authenticated")
             
        # Auto-claim any pending invites for this user (invites are linked to email)
        from app.db.invites import claim_pending_invites
        await claim_pending_invites(user.get("sub"), email)
             
        data = await get_user_environments(user.get("sub"))
        return data
    except Exception as e:
        logger.error(f"Error fetching dashboard environments: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/themes")
async def get_my_themes(user: dict = Depends(get_current_user)):
    """
    Returns a flat list of themes for the dashboard grid.
    Enhanced with metadata (Org, Project, Stats).
    """
    try:
        email = user.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="User not authenticated")
            
        from app.db.dashboard import get_user_themes
        data = await get_user_themes(user.get("sub"))
        return data
    except Exception as e:
        logger.error(f"Error fetching dashboard themes: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
