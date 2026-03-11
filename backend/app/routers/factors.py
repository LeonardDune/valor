from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel
import logging

from app.auth import get_current_user
from app.models.domain import Role
from app.db.crud import (
    create_factor_manual, update_factor_manual, delete_factor_manual,
    get_project_id_by_factor, get_version_id_by_factor, get_project_id_by_theme,
    get_active_version_id_if_theme, get_factors_for_theme, check_permission,
)
from app.services.connection_manager import manager
from app.services.fuseki_sync import try_write_factor

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
    return await get_factors_for_theme(theme_id)


@router.get("/versions/{version_id}/factors")
async def list_version_factors(version_id: str):
    from app.db.crud import get_factors_for_version
    return await get_factors_for_version(version_id)


@router.post("/factors")
async def create_factor(factor: FactorManualCreate, user: dict = Depends(get_current_user)):
    logger.info(f"Creating factor: {factor} by {user['id']}")
    version_id = await get_active_version_id_if_theme(factor.theme_id) if factor.theme_id else None
    project_id_check = await get_project_id_by_theme(factor.theme_id) if factor.theme_id else None
    check_entity = version_id or project_id_check
    if not check_entity or not await check_permission(user["id"], check_entity, Role.MEMBER):
        raise HTTPException(status_code=403, detail="Geen toegang om een factor aan te maken")
    fid = await create_factor_manual(factor.name, factor.description, factor.type or "systeemelement", factor.theme_id, author_id=user["id"])
    await try_write_factor(fid, factor.name, factor.theme_id or "", user["id"])

    if project_id_check:
        await manager.broadcast_data(project_id_check, {
            "type": "FACTOR_CREATED",
            "payload": {"id": fid, "name": factor.name, "description": factor.description, "type": factor.type, "theme_id": factor.theme_id}
        })

    return {"id": fid, "name": factor.name}


@router.patch("/factors/{factor_id}")
async def update_factor_route(factor_id: str, factor: FactorUpdate, user: dict = Depends(get_current_user)):
    project_id = await get_project_id_by_factor(factor_id)
    version_id = await get_version_id_by_factor(factor_id)
    check_entity = version_id or project_id
    if not check_entity or not await check_permission(user["id"], check_entity, Role.MEMBER):
        raise HTTPException(status_code=403, detail="Geen toegang om deze factor te wijzigen")
    await update_factor_manual(factor_id, factor.name, factor.description, factor.type, factor.theme_id)
    if project_id:
        await manager.broadcast_data(project_id, {
            "type": "FACTOR_UPDATED",
            "payload": {"id": factor_id, "changes": factor.dict(exclude_unset=True)}
        })
    return {"status": "updated"}


@router.delete("/factors/{factor_id}")
async def delete_factor_route(factor_id: str, user: dict = Depends(get_current_user)):
    project_id = await get_project_id_by_factor(factor_id)
    version_id = await get_version_id_by_factor(factor_id)
    check_entity = version_id or project_id
    if not check_entity or not await check_permission(user["id"], check_entity, Role.MEMBER):
        raise HTTPException(status_code=403, detail="Geen toegang om deze factor te verwijderen")
    await delete_factor_manual(factor_id)
    if project_id:
        await manager.broadcast_data(project_id, {
            "type": "FACTOR_DELETED",
            "payload": {"id": factor_id}
        })
    return {"status": "deleted"}
