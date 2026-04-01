"""Entity Registry API endpoints (US-AI.3 / US-AI.7).

Routes:
  POST /entities/                                 — nieuwe entiteit aanmaken
  GET  /entities/search?q=&type=                  — zoeken in registry
  POST /entities/norms/                           — normatief object aanmaken
  GET  /entities/norms/search?q=&jurisdiction=    — normen zoeken
  GET  /entities/norms/{uri}/cross-perspective    — cross-perspectief verwijzingen
  GET  /entities/{uri:path}                       — entiteitsdata ophalen
  GET  /entities/{uri:path}/roles?ds_id=          — rollen per DesignSpace
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth import get_current_user
from app.db.fuseki_entities import (
    ENTITY_TYPE_MAP,
    assign_role,
    create_entity,
    create_norm_entity,
    get_entity,
    get_norm_cross_perspective,
    get_roles_for_entity,
    search_entities,
    search_norms,
)

router = APIRouter(prefix="/entities", tags=["entities"])


# ---------------------------------------------------------------------------
# Request / Response modellen
# ---------------------------------------------------------------------------

class EntityCreateRequest(BaseModel):
    entity_type: str
    label: str
    properties: Optional[dict] = None
    identifier: Optional[str] = None


class RoleAssignRequest(BaseModel):
    entity_uri: str
    role_uri: str
    ds_id: str
    context: Optional[str] = None


class NormCreateRequest(BaseModel):
    norm_type_uri: str
    label: str
    identifier: str
    jurisdiction: Optional[str] = None
    effective_date: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/", status_code=201)
async def create_entity_endpoint(
    body: EntityCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Maakt een nieuwe entiteit aan in de Entity Registry."""
    if body.entity_type not in ENTITY_TYPE_MAP:
        raise HTTPException(
            status_code=422,
            detail=f"Onbekend entity_type '{body.entity_type}'. Kies uit: {list(ENTITY_TYPE_MAP)}",
        )
    uri = await create_entity(
        entity_type=body.entity_type,
        label=body.label,
        properties=body.properties,
        identifier=body.identifier,
    )
    return {"uri": uri, "entity_type": body.entity_type, "label": body.label}


@router.get("/search")
async def search_entities_endpoint(
    q: str = Query(..., min_length=1),
    type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """Zoekt entiteiten in de registry op basis van label (substring, case-insensitief)."""
    results = await search_entities(query=q, entity_type=type, limit=limit)
    return {"results": results, "count": len(results)}


@router.post("/roles", status_code=201)
async def assign_role_endpoint(
    body: RoleAssignRequest,
    current_user: dict = Depends(get_current_user),
):
    """Wijst een rol toe aan een entiteit in een DesignSpace."""
    await assign_role(
        entity_uri=body.entity_uri,
        role_uri=body.role_uri,
        ds_id=body.ds_id,
        context=body.context,
    )
    return {"status": "ok", "entity_uri": body.entity_uri, "role_uri": body.role_uri, "ds_id": body.ds_id}


@router.post("/norms/", status_code=201)
async def create_norm_endpoint(
    body: NormCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Maakt een normatief object aan in de Entity Registry (ufoc:NormativeDescription subtype)."""
    uri = await create_norm_entity(
        norm_type_uri=body.norm_type_uri,
        label=body.label,
        identifier=body.identifier,
        jurisdiction=body.jurisdiction,
        effective_date=body.effective_date,
    )
    return {"uri": uri, "norm_type_uri": body.norm_type_uri, "label": body.label, "identifier": body.identifier}


@router.get("/norms/search")
async def search_norms_endpoint(
    q: str = Query(..., min_length=1),
    jurisdiction: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """Zoekt normatieve objecten op label of officieel kenmerk, optioneel gefilterd op jurisdictie."""
    results = await search_norms(query=q, jurisdiction=jurisdiction, limit=limit)
    return {"results": results, "count": len(results)}


@router.get("/norms/{uri:path}/cross-perspective")
async def get_norm_cross_perspective_endpoint(
    uri: str,
    current_user: dict = Depends(get_current_user),
):
    """Retourneert alle grafen (DesignSpaces, perspectieven) die naar deze norm-URI verwijzen."""
    if not uri.startswith("urn:"):
        uri = uri.replace("urn:/", "urn:").lstrip("/")
    refs = await get_norm_cross_perspective(uri)
    return {"norm_uri": uri, "references": refs, "count": len(refs)}


@router.get("/{uri:path}/roles")
async def get_entity_roles_endpoint(
    uri: str,
    ds_id: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    """Haalt alle rollen op voor een entiteit in een specifieke DesignSpace."""
    # uri komt binnen als URL-pad zonder leading slash — herstel urn: prefix
    if not uri.startswith("urn:"):
        uri = uri.replace("urn:/", "urn:").lstrip("/")
    roles = await get_roles_for_entity(entity_uri=uri, ds_id=ds_id)
    return {"entity_uri": uri, "ds_id": ds_id, "roles": roles}


@router.get("/{uri:path}")
async def get_entity_endpoint(
    uri: str,
    current_user: dict = Depends(get_current_user),
):
    """Haalt een entiteit op uit de registry op basis van URI."""
    if not uri.startswith("urn:"):
        uri = uri.replace("urn:/", "urn:").lstrip("/")
    entity = await get_entity(uri=uri)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Entiteit niet gevonden: {uri}")
    return entity
