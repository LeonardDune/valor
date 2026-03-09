from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel
import logging

from app.auth import get_current_user
from app.models.domain import Role
from app.db.crud import (
    create_claim_manual, update_claim_manual, delete_claim_manual,
    get_project_id_by_claim, get_project_id_by_theme,
    get_claims_for_theme, check_permission,
)
from app.services.connection_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


class ClaimManualCreate(BaseModel):
    theme_id: str
    source_id: str
    target_id: str
    statement: str
    polarity: Optional[str] = "+"
    confidence: Optional[float] = 1.0
    evidence_text: Optional[str] = None
    evidence_url: Optional[str] = None


class ClaimUpdate(BaseModel):
    statement: Optional[str] = None
    polarity: Optional[str] = None
    confidence: Optional[float] = None
    source_id: Optional[str] = None
    target_id: Optional[str] = None
    evidence_text: Optional[str] = None
    evidence_url: Optional[str] = None


@router.get("/themes/{theme_id}/claims")
async def list_theme_claims(theme_id: str):
    return await get_claims_for_theme(theme_id)


@router.get("/versions/{version_id}/claims")
async def list_version_claims(version_id: str):
    from app.db.crud import get_claims_for_version
    return await get_claims_for_version(version_id)


@router.post("/claims_manual")
async def create_claim(claim: ClaimManualCreate, user: dict = Depends(get_current_user)):
    logger.info(f"Creating claim: {claim} by {user['id']}")
    cid = await create_claim_manual(
        claim.theme_id,
        claim.source_id,
        claim.target_id,
        claim.statement,
        user["id"],
        claim.polarity,
        claim.confidence,
        claim.evidence_text,
        claim.evidence_url
    )
    if claim.theme_id:
        project_id = await get_project_id_by_theme(claim.theme_id)
        if project_id:
            await manager.broadcast_data(project_id, {
                "type": "CLAIM_CREATED",
                "payload": {"id": cid, "source_id": claim.source_id, "target_id": claim.target_id, "theme_id": claim.theme_id, "statement": claim.statement, "evidence_text": claim.evidence_text, "evidence_url": claim.evidence_url}
            })

    return {"status": "created", "id": cid}


@router.patch("/claims/{claim_id}")
async def update_claim_route(claim_id: str, claim: ClaimUpdate, user: dict = Depends(get_current_user)):
    project_id = await get_project_id_by_claim(claim_id)
    if not project_id or not await check_permission(user["id"], project_id, Role.MEMBER):
        raise HTTPException(status_code=403, detail="Geen toegang om deze claim te wijzigen")
    await update_claim_manual(
        claim_id,
        claim.statement,
        claim.polarity,
        claim.confidence,
        claim.source_id,
        claim.target_id,
        claim.evidence_text,
        claim.evidence_url
    )
    if project_id:
        await manager.broadcast_data(project_id, {
            "type": "CLAIM_UPDATED",
            "payload": {"id": claim_id, "changes": claim.dict(exclude_unset=True)}
        })
    return {"status": "updated"}


@router.delete("/claims/{claim_id}")
async def delete_claim_route(claim_id: str, user: dict = Depends(get_current_user)):
    project_id = await get_project_id_by_claim(claim_id)
    if not project_id or not await check_permission(user["id"], project_id, Role.MEMBER):
        raise HTTPException(status_code=403, detail="Geen toegang om deze claim te verwijderen")
    await delete_claim_manual(claim_id)
    if project_id:
        await manager.broadcast_data(project_id, {
            "type": "CLAIM_DELETED",
            "payload": {"id": claim_id}
        })
    return {"status": "deleted"}
