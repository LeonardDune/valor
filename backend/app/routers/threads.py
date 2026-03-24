"""Discussiethreads router — Fuseki-backed (Epic 16, US-16.2 / US-16.3 / US-16.4).

Vervangt de Neo4j-implementatie. Threads, bijdragen en resoluties worden opgeslagen als
disc:DiscussionThread / disc:ThreadContribution / disc:ThreadResolution in de named graph
van de DesignSpace.
"""
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth import get_current_user
from app.db.designspace import get_design_space_meta
from app.db.disc import (
    create_discussion_thread,
    get_threads_by_tessera,
    create_thread_contribution,
    get_contributions_by_thread,
    get_thread_tessera,
    create_thread_resolution,
)
from app.db.permissions import check_permission
from app.models.domain import Role
from app.services.connection_manager import manager
from app.services.fuseki import sparql_select, sparql_update, named_graph_uri, record_provenance_activity
from app.services.ontology_cache import (
    get_disc_contribution_type_label_to_uri,
    get_status_label_to_uri,
    get_status_uri_to_label,
)
from app.ontology import VALOR_NS

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["threads"],
    responses={404: {"description": "Not found"}},
)


class CreateThreadRequest(BaseModel):
    tessera_id: str
    design_space_id: str
    title: Optional[str] = None


class ThreadResponse(BaseModel):
    thread_id: str
    thread_uri: str
    tessera_id: str
    design_space_id: str
    started_by: str
    started_by_name: str
    started_at: str
    title: Optional[str] = None


@router.post("/threads", response_model=dict[str, str], status_code=201)
async def create_thread(
    request: CreateThreadRequest,
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    user_id = user["id"]
    has_permission = await check_permission(user_id, request.design_space_id, Role.MEMBER)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Onvoldoende rechten om een discussiethread aan te maken.")

    thread_id = await create_discussion_thread(
        tessera_id=request.tessera_id,
        design_space_id=request.design_space_id,
        user_id=user_id,
        title=request.title,
    )
    return {"thread_id": thread_id}


@router.get("/threads", response_model=list[ThreadResponse])
async def list_threads(
    tessera_id: str = Query(..., description="ID van de Tessera"),
    design_space_id: str = Query(..., description="ID van de DesignSpace"),
    user: dict = Depends(get_current_user),
) -> list[dict[str, Any]]:
    user_id = user["id"]
    has_permission = await check_permission(user_id, design_space_id, Role.MEMBER)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Onvoldoende rechten om threads op te halen.")

    return await get_threads_by_tessera(tessera_id=tessera_id, design_space_id=design_space_id)


class CreateContributionRequest(BaseModel):
    design_space_id: str
    contribution_type: str  # Dutch label: "Vraag" | "Stelling" | "Bewijs" | "Bezwaar" | "Toelichting" | "Akkoord"
    message_content: str
    evidence_id: Optional[str] = None


class ContributionResponse(BaseModel):
    contribution_id: str
    contribution_uri: str
    thread_id: str
    design_space_id: str
    contribution_type: str
    message_content: str
    contributed_by: str
    contributed_by_name: str
    contributed_at: str
    evidence_id: Optional[str] = None


@router.post("/threads/{thread_id}/contribute", response_model=dict[str, str], status_code=201)
async def add_contribution(
    thread_id: str,
    request: CreateContributionRequest,
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    user_id = user["id"]
    has_permission = await check_permission(user_id, request.design_space_id, Role.MEMBER)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Onvoldoende rechten om een bijdrage toe te voegen.")

    contribution_type_map = get_disc_contribution_type_label_to_uri()
    contribution_type_uri = contribution_type_map.get(request.contribution_type)
    if not contribution_type_uri:
        valid = sorted(contribution_type_map.keys())
        raise HTTPException(
            status_code=422,
            detail=f"Ongeldig bijdragetype '{request.contribution_type}'. Geldige waarden: {valid}.",
        )

    contrib_id = await create_thread_contribution(
        thread_id=thread_id,
        design_space_id=request.design_space_id,
        user_id=user_id,
        contribution_type_uri=contribution_type_uri,
        message_content=request.message_content,
        evidence_id=request.evidence_id,
    )
    return {"contribution_id": contrib_id}


@router.get("/threads/{thread_id}/contributions", response_model=list[ContributionResponse])
async def list_contributions(
    thread_id: str,
    design_space_id: str = Query(..., description="ID van de DesignSpace"),
    user: dict = Depends(get_current_user),
) -> list[dict[str, Any]]:
    user_id = user["id"]
    has_permission = await check_permission(user_id, design_space_id, Role.MEMBER)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Onvoldoende rechten om bijdragen op te halen.")

    return await get_contributions_by_thread(thread_id=thread_id, design_space_id=design_space_id)


class ResolveThreadRequest(BaseModel):
    design_space_id: str
    resolution_outcome: str   # English label: bijv. "Contested", "Accepted", "Rejected"
    resolution_rationale: str


class ResolveThreadResponse(BaseModel):
    resolution_id: str
    thread_id: str
    tessera_id: str
    previous_status: str
    new_status: str


@router.post("/threads/{thread_id}/resolve", response_model=ResolveThreadResponse)
async def resolve_thread(
    thread_id: str,
    request: ResolveThreadRequest,
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    user_id = user["id"]
    has_permission = await check_permission(user_id, request.design_space_id, Role.MODERATOR)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Onvoldoende rechten om een thread te resolveren. Moderator-rol vereist.")

    # Haal tessera_uri op uit de thread
    tessera_uri = await get_thread_tessera(thread_id, request.design_space_id)
    if not tessera_uri:
        raise HTTPException(status_code=404, detail="Thread niet gevonden in deze DesignSpace.")
    tessera_id = tessera_uri.split(":")[-1]

    # Valideer resolution_outcome als geldige epistemische status
    status_label_to_uri = get_status_label_to_uri()
    new_status_uri = status_label_to_uri.get(request.resolution_outcome)
    if not new_status_uri:
        raise HTTPException(
            status_code=422,
            detail=f"Ongeldig resolution_outcome '{request.resolution_outcome}'. Geldige waarden: {sorted(status_label_to_uri)}.",
        )

    # Lees huidige status van de Tessera
    graph_uri = named_graph_uri(request.design_space_id)
    status_rows = await sparql_select(
        f"""SELECT ?status WHERE {{
          GRAPH <{graph_uri}> {{
            <{tessera_uri}> <{VALOR_NS}epistemicStatus> ?status .
          }}
        }}""",
        request.design_space_id,
    )
    # Als de tessera nog geen epistemicStatus heeft (bijv. Neo4j-factor waarvoor nog geen
    # Fuseki-Tessera bestaat), val terug op "Proposed" als initiële status.
    proposed_uri = status_label_to_uri.get("Proposed", f"{VALOR_NS}ProposedStatus")

    if status_rows:
        current_uri = status_rows[0]["status"]
        current_label = get_status_uri_to_label().get(current_uri, current_uri)
        status_sparql = f"""DELETE {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> <{VALOR_NS}epistemicStatus> <{current_uri}> .
  }}
}}
INSERT {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> <{VALOR_NS}epistemicStatus> <{new_status_uri}> .
  }}
}}
WHERE {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> <{VALOR_NS}epistemicStatus> <{current_uri}> .
  }}
}}"""
    else:
        current_uri = proposed_uri
        current_label = "Proposed"
        status_sparql = f"""INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> <{VALOR_NS}epistemicStatus> <{new_status_uri}> .
  }}
}}"""

    # Schrijf disc:ThreadResolution naar Fuseki
    resolution_id = await create_thread_resolution(
        thread_id=thread_id,
        design_space_id=request.design_space_id,
        user_id=user_id,
        resolution_outcome_uri=new_status_uri,
        resolution_rationale=request.resolution_rationale,
        tessera_uri=tessera_uri,
    )

    # Wijzig epistemische status van de Tessera
    await sparql_update(status_sparql, request.design_space_id)

    # PROV-O record
    await record_provenance_activity(
        request.design_space_id,
        "StatusChanged",
        f"urn:valor:user:{user_id}",
        used=[tessera_uri],
        extra_props=[
            (f"{VALOR_NS}previousStatus", current_uri),
            (f"{VALOR_NS}newStatus", new_status_uri),
        ],
    )

    # WebSocket broadcast
    ds_meta = get_design_space_meta(request.design_space_id)
    project_id = ds_meta.get("project_id") if ds_meta else None
    if project_id:
        await manager.broadcast_data(project_id, {
            "type": "TESSERA_STATUS_CHANGED",
            "payload": {
                "tessera_id": tessera_id,
                "tessera_uri": tessera_uri,
                "previous_status": current_label,
                "new_status": request.resolution_outcome,
                "resolution_id": resolution_id,
                "thread_id": thread_id,
                "design_space_id": request.design_space_id,
            },
        })

    logger.info(
        "ThreadResolution %s: thread %s → tessera %s status %s → %s (door %s)",
        resolution_id, thread_id, tessera_id, current_label, request.resolution_outcome, user_id,
    )

    return ResolveThreadResponse(
        resolution_id=resolution_id,
        thread_id=thread_id,
        tessera_id=tessera_id,
        previous_status=current_label,
        new_status=request.resolution_outcome,
    )
