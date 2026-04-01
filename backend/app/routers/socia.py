"""SOCIA API-endpoints voor het cross-perspectief rolpatroon (US-AI.5)."""
from fastapi import APIRouter, Depends, Query

from app.auth import get_current_user
from app.db.fuseki_socia import (
    assign_actor_role,
    get_actor_roles_in_ds,
    get_designspaces_for_agent,
    get_tesserae_for_agent,
)

router = APIRouter(tags=["socia"])


@router.post("/designspace/{ds_id}/socia/roles")
async def assign_role_endpoint(
    ds_id: str,
    entity_uri: str,
    role_uri: str,
    _user=Depends(get_current_user),
):
    """Wijst een socia:playsRole toe aan een agent in een DesignSpace."""
    await assign_actor_role(entity_uri, role_uri, ds_id)
    return {"status": "ok", "entity_uri": entity_uri, "role_uri": role_uri, "ds_id": ds_id}


@router.get("/designspace/{ds_id}/socia/roles")
async def get_roles_endpoint(
    ds_id: str,
    _user=Depends(get_current_user),
):
    """Retourneert alle actor-rol-paren in een DesignSpace."""
    return await get_actor_roles_in_ds(ds_id)


@router.get("/designspace/{ds_id}/socia/actors/{actor_uri:path}/tesserae")
async def get_actor_tesserae_endpoint(
    ds_id: str,
    actor_uri: str,
    _user=Depends(get_current_user),
):
    """Retourneert alle Tesserae in een DesignSpace waarop de agent is geclaimed (cross-perspectief)."""
    if not actor_uri.startswith("urn:"):
        actor_uri = actor_uri.replace("urn:/", "urn:").lstrip("/")
    return await get_tesserae_for_agent(actor_uri, ds_id)


@router.get("/agents/{agent_uri:path}/designspaces")
async def get_agent_designspaces_endpoint(
    agent_uri: str,
    _user=Depends(get_current_user),
):
    """Retourneert alle DesignSpace-IDs waar de agent een socia:playsRole heeft."""
    if not agent_uri.startswith("urn:"):
        agent_uri = agent_uri.replace("urn:/", "urn:").lstrip("/")
    ds_ids = await get_designspaces_for_agent(agent_uri)
    return {"agent_uri": agent_uri, "designspaces": ds_ids}
