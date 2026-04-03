"""SOCIA API-endpoints voor het cross-perspectief rolpatroon (US-AI.5/AI.6)."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth import get_current_user
from app.db.fuseki_socia import (
    assign_actor_role,
    create_stakeholder_claim,
    get_actor_roles_in_ds,
    get_designspaces_for_agent,
    get_stakeholder_map,
    get_tesserae_for_agent,
    migrate_legacy_socia_actors,
)
from app.db.permissions import check_permission
from app.models.domain import Role

router = APIRouter(tags=["socia"])


class CreateStakeholderClaimRequest(BaseModel):
    claim_type: str  # "InterestClaim" | "GoalClaim" | "PowerClaim"
    claim_content: str
    actor_uri: str  # URI van de actor waarover de claim gaat


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


@router.get("/designspace/{ds_id}/stakeholder-map")
async def get_stakeholder_map_endpoint(
    ds_id: str,
    _user=Depends(get_current_user),
):
    """Retourneert de stakeholderkaart: actoren en IntentionalDependency-edges voor een DesignSpace."""
    return await get_stakeholder_map(ds_id)


@router.post("/designspace/{ds_id}/stakeholder-claims", status_code=201)
async def create_stakeholder_claim_endpoint(
    ds_id: str,
    request: CreateStakeholderClaimRequest,
    user: dict = Depends(get_current_user),
):
    """Maakt een socia:InterestClaim, socia:GoalClaim of socia:PowerClaim aan als Tessera-subklasse."""
    has_permission = await check_permission(user["id"], ds_id, Role.MEMBER)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Onvoldoende rechten voor deze DesignSpace.")

    try:
        result = await create_stakeholder_claim(
            ds_id=ds_id,
            claim_type=request.claim_type,
            claim_content=request.claim_content,
            actor_uri=request.actor_uri,
            user_id=user["id"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return result


@router.post("/admin/migrate-socia-actors")
async def migrate_socia_actors_endpoint(user=Depends(get_current_user)):
    """Migreert legacy socia:Actor-resources naar het Entity Registry patroon.

    Idempotent — veilig om meerdere keren uit te voeren.
    Vereist platform-admin rechten.
    """
    if not getattr(user, "is_platform_admin", False):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Alleen platformbeheerders kunnen deze migratie uitvoeren.")
    return await migrate_legacy_socia_actors()
