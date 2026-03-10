import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_user
from app.db.permissions import check_permission
from app.models.domain import Role
from app.services.fuseki import sparql_update, named_graph_uri
from app.ontology import VALOR_NS

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tessera",
    tags=["tessera"],
)

XSD_NS = "http://www.w3.org/2001/XMLSchema#"


class CreateTesseraRequest(BaseModel):
    design_space_id: str
    claim_content: str
    claim_type: str  # "AsIs" | "ToBe"
    in_alternative: Optional[str] = None
    in_phase: Optional[str] = None


class TesseraResponse(BaseModel):
    tessera_id: str
    tessera_uri: str
    design_space_id: str
    claim_content: str
    claim_type: str
    epistemic_status: str
    claimed_by: str
    claimed_at: str


@router.post("/", response_model=TesseraResponse, status_code=201)
async def create_tessera(
    request: CreateTesseraRequest,
    user: dict = Depends(get_current_user),
):
    if request.claim_type not in ("AsIs", "ToBe"):
        raise HTTPException(
            status_code=422,
            detail="claim_type moet 'AsIs' of 'ToBe' zijn.",
        )

    user_id = user["id"]

    has_permission = await check_permission(user_id, request.design_space_id, Role.MEMBER)
    if not has_permission:
        raise HTTPException(
            status_code=403,
            detail="Onvoldoende rechten voor deze DesignSpace.",
        )

    tessera_id = str(uuid.uuid4())
    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    user_uri = f"urn:valor:user:{user_id}"
    graph_uri = named_graph_uri(request.design_space_id)
    claimed_at = datetime.now(timezone.utc).isoformat()

    optional_triples = ""
    if request.in_alternative:
        alt_uri = f"urn:valor:alternative:{request.in_alternative}"
        optional_triples += f"      <{tessera_uri}> <{VALOR_NS}inAlternative> <{alt_uri}> .\n"
    if request.in_phase:
        phase_uri = f"urn:valor:phase:{request.in_phase}"
        optional_triples += f"      <{tessera_uri}> <{VALOR_NS}inPhase> <{phase_uri}> .\n"

    escaped_content = request.claim_content.replace("\\", "\\\\").replace('"', '\\"')

    sparql = f"""PREFIX valor: <{VALOR_NS}>
PREFIX xsd: <{XSD_NS}>

INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> a valor:Tessera ;
      valor:claimContent "{escaped_content}"@nl ;
      valor:epistemicStatus "Proposed" ;
      valor:claimType "{request.claim_type}" ;
      valor:claimedBy <{user_uri}> ;
      valor:claimedAt "{claimed_at}"^^xsd:dateTime ;
      valor:inDesignSpace <{graph_uri}> .
{optional_triples}  }}
}}"""

    await sparql_update(sparql, request.design_space_id)

    logger.info("Tessera aangemaakt: %s in DesignSpace %s door %s", tessera_uri, request.design_space_id, user_id)

    return TesseraResponse(
        tessera_id=tessera_id,
        tessera_uri=tessera_uri,
        design_space_id=request.design_space_id,
        claim_content=request.claim_content,
        claim_type=request.claim_type,
        epistemic_status="Proposed",
        claimed_by=user_id,
        claimed_at=claimed_at,
    )
