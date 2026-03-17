"""Discussiethreads router — Fuseki-backed (Epic 16, US-16.2 / US-16.3).

Vervangt de Neo4j-implementatie. Threads en bijdragen worden opgeslagen als
disc:DiscussionThread / disc:ThreadContribution in de named graph van de DesignSpace.
"""
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth import get_current_user
from app.db.disc import (
    create_discussion_thread,
    get_threads_by_tessera,
    create_thread_contribution,
    get_contributions_by_thread,
)
from app.db.permissions import check_permission
from app.models.domain import Role
from app.services.ontology_cache import get_disc_contribution_type_label_to_uri

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["threads"],
    responses={404: {"description": "Not found"}},
)


class CreateThreadRequest(BaseModel):
    tessera_id: str
    design_space_id: str


class ThreadResponse(BaseModel):
    thread_id: str
    thread_uri: str
    tessera_id: str
    design_space_id: str
    started_by: str
    started_at: str


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
