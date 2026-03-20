from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel
import logging

from app.auth import get_current_user
from app.models.domain import Role
from app.db.crud import (
    get_project_id_by_theme,
    get_active_version_id_if_theme,
    check_permission,
)
from app.db import fuseki_knowledge
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
    return await fuseki_knowledge.get_claims_for_theme(theme_id)


@router.get("/versions/{version_id}/claims")
async def list_version_claims(version_id: str):
    return await fuseki_knowledge.get_claims_for_version(version_id)


@router.post("/claims_manual")
async def create_claim(claim: ClaimManualCreate, user: dict = Depends(get_current_user)):
    logger.info("Creating claim by %s in theme %s", user["id"], claim.theme_id)

    version_id = await get_active_version_id_if_theme(claim.theme_id) if claim.theme_id else None
    project_id = await get_project_id_by_theme(claim.theme_id) if claim.theme_id else None
    ds_id = await fuseki_knowledge.get_designspace_id_for_version(version_id) if version_id else None

    check_entity = ds_id or project_id
    if not check_entity or not await check_permission(user["id"], check_entity, Role.MEMBER):
        raise HTTPException(status_code=403, detail="Geen toegang om een claim aan te maken")
    if not ds_id:
        raise HTTPException(status_code=422, detail="Geen actieve DesignSpace gevonden voor dit thema")

    cid = await fuseki_knowledge.create_claim_fuseki(
        ds_id=ds_id,
        source_id=claim.source_id,
        target_id=claim.target_id,
        statement=claim.statement,
        polarity=claim.polarity or "+",
        user_id=user["id"],
        confidence=claim.confidence or 1.0,
        evidence_text=claim.evidence_text,
        evidence_url=claim.evidence_url,
    )

    if project_id:
        await manager.broadcast_data(project_id, {
            "type": "CLAIM_CREATED",
            "payload": {
                "id": cid,
                "source_id": claim.source_id,
                "target_id": claim.target_id,
                "theme_id": claim.theme_id,
                "statement": claim.statement,
                "evidence_text": claim.evidence_text,
                "evidence_url": claim.evidence_url,
            },
        })

    return {"status": "created", "id": cid}


@router.patch("/claims/{claim_id}")
async def update_claim_route(claim_id: str, claim: ClaimUpdate, user: dict = Depends(get_current_user)):
    ds_id = await fuseki_knowledge.get_designspace_id_for_tessera(claim_id)
    if not ds_id:
        raise HTTPException(status_code=404, detail="Claim niet gevonden")
    if not await check_permission(user["id"], ds_id, Role.MEMBER):
        raise HTTPException(status_code=403, detail="Geen toegang om deze claim te wijzigen")

    await fuseki_knowledge.update_claim_fuseki(
        tessera_id=claim_id,
        ds_id=ds_id,
        statement=claim.statement,
        polarity=claim.polarity,
        confidence=claim.confidence,
        evidence_text=claim.evidence_text,
    )

    project_id = await fuseki_knowledge.get_project_id_for_designspace(ds_id)
    if project_id:
        await manager.broadcast_data(project_id, {
            "type": "CLAIM_UPDATED",
            "payload": {"id": claim_id, "changes": claim.dict(exclude_unset=True)},
        })

    return {"status": "updated"}


@router.delete("/claims/{claim_id}")
async def delete_claim_route(claim_id: str, user: dict = Depends(get_current_user)):
    ds_id = await fuseki_knowledge.get_designspace_id_for_tessera(claim_id)
    if not ds_id:
        raise HTTPException(status_code=404, detail="Claim niet gevonden")
    if not await check_permission(user["id"], ds_id, Role.MEMBER):
        raise HTTPException(status_code=403, detail="Geen toegang om deze claim te verwijderen")

    await fuseki_knowledge.delete_claim_fuseki(tessera_id=claim_id, ds_id=ds_id)

    project_id = await fuseki_knowledge.get_project_id_for_designspace(ds_id)
    if project_id:
        await manager.broadcast_data(project_id, {
            "type": "CLAIM_DELETED",
            "payload": {"id": claim_id},
        })

    return {"status": "deleted"}
