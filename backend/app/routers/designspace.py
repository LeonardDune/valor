import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.auth import get_current_user
from app.db.designspace import create_design_space as db_create_design_space
from app.db.permissions import check_permission
from app.models.domain import DesignSpaceCreate, DesignSpaceResponse, Role
from app.services.fuseki import initialize_design_space_graphs, sparql_proxy_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/designspace", tags=["designspace"])


@router.post("/", response_model=DesignSpaceResponse, status_code=201)
async def create_design_space(
    request: DesignSpaceCreate,
    user: dict = Depends(get_current_user),
) -> DesignSpaceResponse:
    user_id = user["id"]

    if request.project_id:
        if not await check_permission(user_id, request.project_id, Role.MEMBER):
            raise HTTPException(
                status_code=403,
                detail="Onvoldoende rechten voor dit project.",
            )

    ds_id = await db_create_design_space(
        name=request.name,
        description=request.description,
        issue_uri=request.issue_uri,
        owner_id=user_id,
        project_id=request.project_id,
    )

    named_graphs = await initialize_design_space_graphs(ds_id, request.issue_uri)

    logger.info("DesignSpace aangemaakt: %s door gebruiker %s", ds_id, user_id)

    return DesignSpaceResponse(
        id=ds_id,
        name=request.name,
        description=request.description,
        issue_uri=request.issue_uri,
        design_space_uri=f"urn:valor:ds:{ds_id}",
        named_graphs=named_graphs,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/{design_space_id}/sparql")
async def sparql_query(
    design_space_id: str,
    query: str = Query(..., description="SPARQL SELECT/CONSTRUCT/ASK/DESCRIBE query"),
    user: dict = Depends(get_current_user),
) -> JSONResponse:
    user_id = user["id"]

    if not await check_permission(user_id, design_space_id, Role.VIEWER):
        raise HTTPException(
            status_code=403,
            detail="Onvoldoende rechten voor deze DesignSpace.",
        )

    result = await sparql_proxy_query(query, design_space_id)

    logger.info("SPARQL proxy: DesignSpace %s bevraagd door gebruiker %s", design_space_id, user_id)

    return JSONResponse(content=result)
