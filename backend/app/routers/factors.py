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


class FactorManualCreate(BaseModel):
    name: str
    description: Optional[str] = None
    type: Optional[str] = "systeemelement"
    theme_id: Optional[str] = None


class FactorUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    theme_id: Optional[str] = None


@router.get("/themes/{theme_id}/factors")
async def list_theme_factors(theme_id: str):
    return await fuseki_knowledge.get_factors_for_theme(theme_id)


@router.get("/versions/{version_id}/factors")
async def list_version_factors(version_id: str):
    return await fuseki_knowledge.get_factors_for_version(version_id)


@router.post("/factors")
async def create_factor(factor: FactorManualCreate, user: dict = Depends(get_current_user)):
    logger.info("Creating factor: %s by %s", factor.name, user["id"])

    version_id = await get_active_version_id_if_theme(factor.theme_id) if factor.theme_id else None
    project_id = await get_project_id_by_theme(factor.theme_id) if factor.theme_id else None
    ds_id = await fuseki_knowledge.get_designspace_id_for_version(version_id) if version_id else None

    check_entity = ds_id or project_id
    if not check_entity or not await check_permission(user["id"], check_entity, Role.MEMBER):
        raise HTTPException(status_code=403, detail="Geen toegang om een factor aan te maken")
    if not ds_id:
        raise HTTPException(status_code=422, detail="Geen actieve DesignSpace gevonden voor dit thema")

    fid = await fuseki_knowledge.create_factor_fuseki(
        ds_id=ds_id,
        name=factor.name,
        role=factor.type or "systeemelement",
        user_id=user["id"],
        description=factor.description,
    )

    if project_id:
        await manager.broadcast_data(project_id, {
            "type": "FACTOR_CREATED",
            "payload": {
                "id": fid,
                "name": factor.name,
                "description": factor.description,
                "type": factor.type,
                "theme_id": factor.theme_id,
            },
        })

    return {"id": fid, "name": factor.name}


@router.patch("/factors/{factor_id}")
async def update_factor_route(factor_id: str, factor: FactorUpdate, user: dict = Depends(get_current_user)):
    ds_id = await fuseki_knowledge.get_designspace_id_for_tessera(factor_id)
    if not ds_id:
        raise HTTPException(status_code=404, detail="Factor niet gevonden")
    if not await check_permission(user["id"], ds_id, Role.MEMBER):
        raise HTTPException(status_code=403, detail="Geen toegang om deze factor te wijzigen")

    await fuseki_knowledge.update_factor_fuseki(
        tessera_id=factor_id,
        ds_id=ds_id,
        name=factor.name,
        description=factor.description,
        role=factor.type,
    )

    project_id = await fuseki_knowledge.get_project_id_for_designspace(ds_id)
    if project_id:
        await manager.broadcast_data(project_id, {
            "type": "FACTOR_UPDATED",
            "payload": {"id": factor_id, "changes": factor.dict(exclude_unset=True)},
        })

    return {"status": "updated"}


@router.delete("/factors/{factor_id}")
async def delete_factor_route(factor_id: str, user: dict = Depends(get_current_user)):
    ds_id = await fuseki_knowledge.get_designspace_id_for_tessera(factor_id)
    if not ds_id:
        raise HTTPException(status_code=404, detail="Factor niet gevonden")
    if not await check_permission(user["id"], ds_id, Role.MEMBER):
        raise HTTPException(status_code=403, detail="Geen toegang om deze factor te verwijderen")

    await fuseki_knowledge.delete_factor_fuseki(tessera_id=factor_id, ds_id=ds_id)

    project_id = await fuseki_knowledge.get_project_id_for_designspace(ds_id)
    if project_id:
        await manager.broadcast_data(project_id, {
            "type": "FACTOR_DELETED",
            "payload": {"id": factor_id},
        })

    return {"status": "deleted"}
