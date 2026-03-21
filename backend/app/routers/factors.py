from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel
import logging

from app.auth import get_current_user
from app.models.domain import Role
from app.db.crud import check_permission
from app.db import fuseki_knowledge
from app.services.connection_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


class FactorManualCreate(BaseModel):
    name: str
    description: Optional[str] = None
    type: Optional[str] = "systeemelement"
    ds_id: str


class FactorUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None


@router.get("/designspace/{ds_id}/factors")
async def list_designspace_factors(ds_id: str, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], ds_id, Role.MEMBER):
        raise HTTPException(status_code=403, detail="Geen toegang tot deze DesignSpace")
    return await fuseki_knowledge._sparql_get_factors(ds_id)


@router.post("/factors")
async def create_factor(factor: FactorManualCreate, user: dict = Depends(get_current_user)):
    logger.info("Creating factor: %s by %s in ds %s", factor.name, user["id"], factor.ds_id)

    if not await check_permission(user["id"], factor.ds_id, Role.MEMBER):
        raise HTTPException(status_code=403, detail="Geen toegang om een factor aan te maken")

    fid = await fuseki_knowledge.create_factor_fuseki(
        ds_id=factor.ds_id,
        name=factor.name,
        role=factor.type or "systeemelement",
        user_id=user["id"],
        description=factor.description,
    )

    project_id = await fuseki_knowledge.get_project_id_for_designspace(factor.ds_id)
    if project_id:
        await manager.broadcast_data(project_id, {
            "type": "FACTOR_CREATED",
            "payload": {
                "id": fid,
                "name": factor.name,
                "description": factor.description,
                "type": factor.type,
                "ds_id": factor.ds_id,
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
