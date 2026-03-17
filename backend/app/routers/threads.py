"""Discussiethreads router — Fuseki-backed (Epic 16, US-16.2).

Vervangt de Neo4j-implementatie. Threads worden opgeslagen als
disc:DiscussionThread in de named graph van de DesignSpace.
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth import get_current_user
from app.db.disc import create_discussion_thread, get_threads_by_tessera
from app.db.permissions import check_permission
from app.models.domain import Role

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
