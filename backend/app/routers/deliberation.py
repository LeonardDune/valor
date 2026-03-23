from fastapi import APIRouter, Depends, HTTPException, status
from app.auth import get_current_user
from app.db.deliberation import (
    submit_feedback, 
    get_session_feedback, 
    submit_ranking, 
    get_session_rankings, 
    update_session_stage,
    get_eligible_claims_for_ranking,
    get_consent_shortlist,
    submit_consent_vote,
    get_session_participation,
    get_consent_shortlist,
    submit_consent_vote,
    get_session_participation,
    finalize_deliberation,
    validate_phase_transition
)
from app.db.sessions import get_session_context, get_moderator_sessions
from app.db.permissions import check_permission
from app.models.domain import Role, Feedback, Ranking, DeliberationStage, ConsentVote, ConsentVoteType
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.services.connection_manager import manager
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/deliberation", tags=["deliberation"])

class FeedbackRequest(BaseModel):
    session_id: str
    tessera_base_id: str
    color: str
    motivation: Optional[str] = None

class RankingRequest(BaseModel):
    session_id: str
    tessera_base_id: str
    category: str # high, medium, backlog, discard

class ConsentVoteRequest(BaseModel):
    session_id: str
    tessera_base_id: str
    vote: ConsentVoteType
    motivation: Optional[str] = None

class StageUpdateRequest(BaseModel):
    stage: DeliberationStage

@router.post("/feedback")
async def post_feedback(data: FeedbackRequest, user: dict = Depends(get_current_user)):
    user_id = user.get("id")
    
    # 1. Create model
    feedback = Feedback(
        session_id=data.session_id,
        tessera_base_id=data.tessera_base_id,
        user_id=user_id,
        color=data.color,
        motivation=data.motivation
    )
    
    # 2. Store
    success = await submit_feedback(feedback)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to submit feedback")
        
    return {"status": "success"}

@router.get("/feedback/{session_id}")
async def get_feedback(session_id: str, user: dict = Depends(get_current_user)):
    return await get_session_feedback(session_id)

@router.post("/rank")
async def post_ranking(data: RankingRequest, user: dict = Depends(get_current_user)):
    user_id = user.get("id")
    
    ranking = Ranking(
        session_id=data.session_id,
        tessera_base_id=data.tessera_base_id,
        user_id=user_id,
        category=data.category
    )
    
    success = await submit_ranking(ranking)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to submit ranking")
        
    return {"status": "success"}

@router.get("/rankings/{session_id}")
async def get_rankings(session_id: str, user: dict = Depends(get_current_user)):
    return await get_session_rankings(session_id)

@router.get("/session/{session_id}/eligible-claims")
async def get_eligible_claims(session_id: str, user: dict = Depends(get_current_user)):
    return await get_eligible_claims_for_ranking(session_id)

@router.get("/session/{session_id}/consent-shortlist")
async def get_shortlist(session_id: str, user: dict = Depends(get_current_user)):
    return await get_consent_shortlist(session_id, user.get("id"))

@router.post("/session/{session_id}/consent-vote")
async def post_consent_vote(session_id: str, data: ConsentVoteRequest, user: dict = Depends(get_current_user)):
    user_id = user.get("id")
    
    vote_obj = ConsentVote(
        session_id=session_id,
        tessera_base_id=data.tessera_base_id,
        user_id=user_id,
        vote=data.vote,
        motivation=data.motivation
    )
    
    success = await submit_consent_vote(vote_obj)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to submit consent vote")
        
    return {"status": "success"}

@router.patch("/session/{session_id}/stage")
async def update_stage(session_id: str, data: StageUpdateRequest, user: dict = Depends(get_current_user)):
    # 1. Resolve Context
    theme_id, project_id = await get_session_context(session_id)
    if not theme_id:
        raise HTTPException(status_code=404, detail="Session context not found")
        
    # 2. Check Permissions (Moderator+)
    is_allowed = await check_permission(user.get("id"), theme_id, Role.MODERATOR)
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Not authorized to advance session stage")
        
    # 3. Validate Transition
    validation = await validate_phase_transition(session_id, "unknown", data.stage) # current stage not strictly needed for target check logic as implemented
    if not validation["allowed"]:
         raise HTTPException(status_code=400, detail=validation["message"])

    # 4. Update DB
    success = await update_session_stage(session_id, data.stage)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update session stage")
        
    # 4. Broadcast
    if project_id:
        await manager.broadcast_data(project_id, {
            "type": "SESSION_STAGE_UPDATED",
            "payload": {
                "session_id": session_id,
                "stage": data.stage
            }
        })
        
    return {"stage": data.stage}

@router.get("/moderator/sessions")
async def get_moderator_managed_sessions(user: dict = Depends(get_current_user)):
    return await get_moderator_sessions(user.get("id"))

@router.get("/session/{session_id}/participation")
async def get_participation(session_id: str, user: dict = Depends(get_current_user)):
    return await get_session_participation(session_id)

@router.post("/session/{session_id}/finalize")
async def post_finalize(session_id: str, user: dict = Depends(get_current_user)):
    # 1. Resolve Context
    theme_id, project_id = await get_session_context(session_id)
    if not theme_id:
        raise HTTPException(status_code=404, detail="Session context not found")
        
    # 2. Check Permissions (Moderator+)
    is_allowed = await check_permission(user.get("id"), theme_id, Role.MODERATOR)
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Not authorized to finalize session")
        
    # 3. Finalize
    result = await finalize_deliberation(session_id, user.get("id"))
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
        
    # 4. Broadcast
    if project_id:
        await manager.broadcast_data(project_id, {
            "type": "SESSION_FINALIZED",
            "payload": {
                "session_id": session_id,
                "next_version_id": result["next_version_id"]
            }
        })
        
    return result

@router.get("/session/{session_id}/transition-validation")
async def get_transition_validation(session_id: str, target_stage: DeliberationStage, user: dict = Depends(get_current_user)):
    return await validate_phase_transition(session_id, "unknown", target_stage)
