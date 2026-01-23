from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.models.domain import Proposal, LifecycleStatus
from app.db.crud import create_proposal, get_proposals, get_proposal_by_id, update_proposal_status
import logging

router = APIRouter(
    prefix="/proposals",
    tags=["proposals"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)

# Pydantic models for request body
from pydantic import BaseModel

class CreateProposalRequest(BaseModel):
    title: str
    description: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = "standard" # standard, access_request, etc
    author_id: str
    target_id: Optional[str] = None # For ACCESS_REQUEST: entity_id

class UpdateProposalStatusRequest(BaseModel):
    status: LifecycleStatus

@router.post("/", response_model=str)
async def create_new_proposal(request: CreateProposalRequest):
    try:
        pid = await create_proposal(request.title, request.author_id, request.description, request.type, request.target_id)
        return pid
    except Exception as e:
        logger.error(f"Error creating proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[Proposal])
async def list_proposals(status: Optional[str] = None, author: Optional[str] = None):
    try:
        return await get_proposals(status, author_id=author)
    except Exception as e:
        logger.error(f"Error listing proposals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{proposal_id}", response_model=Proposal)
async def get_proposal(proposal_id: str):
    p = await get_proposal_by_id(proposal_id)
    if not p:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return p

@router.put("/{proposal_id}/status")
async def update_status(proposal_id: str, request: UpdateProposalStatusRequest):
    success = await update_proposal_status(proposal_id, request.status)
    if not success:
         # Could be not found or error, let's assume not found for simplicity or check logic
         raise HTTPException(status_code=404, detail="Proposal not found or update failed")
    # If ACCESS_REQUEST is accepted, trigger membership logic
    # This requires checking the proposal type first.
    # Ideally, move this to a service layer, but for now:
    repo_proposal = await get_proposal_by_id(proposal_id)
    
    if success and request.status == LifecycleStatus.ACCEPTED and repo_proposal:
         # TODO: Check if type is ACCESS_REQUEST and call add_member
         # This needs expansion in CRUD to support type/target_id storage first.
         pass

    return {"status": "updated", "new_status": request.status}
