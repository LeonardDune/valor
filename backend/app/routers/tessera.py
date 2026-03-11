import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_user
from app.db.permissions import check_permission
from app.models.domain import Role
from app.services.fuseki import sparql_select, sparql_update, named_graph_uri
from app.ontology import VALOR_NS

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tessera",
    tags=["tessera"],
)

XSD_NS = "http://www.w3.org/2001/XMLSchema#"

# Ontologie-base voor named individuals (valor:ProposedStatus etc.)
# Dit is de `valor:` prefix zoals gedefinieerd in de VALOR-O ontologie.
_ONTOLOGY_BASE = os.getenv("VALOR_ONTOLOGY_BASE_URL", "https://valor-ecosystem.nl/ontology/")

EPISTEMIC_STATUS_URIS: dict[str, str] = {
    "Proposed":     f"{_ONTOLOGY_BASE}ProposedStatus",
    "Contested":    f"{_ONTOLOGY_BASE}ContestedStatus",
    "Accepted":     f"{_ONTOLOGY_BASE}AcceptedStatus",
    "Rejected":     f"{_ONTOLOGY_BASE}RejectedStatus",
    "Reconsidered": f"{_ONTOLOGY_BASE}ReconsideredStatus",
}

_STATUS_URI_TO_NAME: dict[str, str] = {v: k for k, v in EPISTEMIC_STATUS_URIS.items()}

# Statusmachine conform DD-065
VALID_TRANSITIONS: dict[str, set[str]] = {
    "Proposed":     {"Contested", "Accepted", "Rejected"},
    "Contested":    {"Accepted", "Rejected"},
    "Accepted":     {"Reconsidered"},
    "Rejected":     {"Reconsidered"},
    "Reconsidered": {"Proposed"},
}

REQUIRES_DECISION_EPISODE = {"Accepted", "Rejected"}

EVIDENCE_TYPES = {"Empirical", "Theoretical", "Expert", "Experiential"}


def _normalize_status(raw: str) -> str:
    """Vertaalt een URI of legacy string-literal naar de canonieke statusnaam."""
    return _STATUS_URI_TO_NAME.get(raw, raw)


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


class CreateEvidenceRequest(BaseModel):
    design_space_id: str
    evidence_type: str  # Empirical | Theoretical | Expert | Experiential
    strength: str
    source: str


class EvidenceResponse(BaseModel):
    evidence_id: str
    evidence_uri: str
    tessera_id: str
    tessera_uri: str
    evidence_type: str
    strength: str
    source: str
    added_by: str
    added_at: str


class PatchTesseraStatusRequest(BaseModel):
    design_space_id: str
    new_status: str
    decision_episode_uri: Optional[str] = None


class PatchTesseraStatusResponse(BaseModel):
    tessera_id: str
    tessera_uri: str
    previous_status: str
    new_status: str


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
    proposed_uri = EPISTEMIC_STATUS_URIS["Proposed"]

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
      valor:epistemicStatus <{proposed_uri}> ;
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


@router.patch("/{tessera_id}/status", response_model=PatchTesseraStatusResponse)
async def patch_tessera_status(
    tessera_id: str,
    request: PatchTesseraStatusRequest,
    user: dict = Depends(get_current_user),
):
    if request.new_status not in VALID_TRANSITIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Ongeldig doelstatus '{request.new_status}'. Geldige waarden: {sorted(VALID_TRANSITIONS)}.",
        )

    user_id = user["id"]

    has_permission = await check_permission(user_id, request.design_space_id, Role.MEMBER)
    if not has_permission:
        raise HTTPException(
            status_code=403,
            detail="Onvoldoende rechten voor deze DesignSpace.",
        )

    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    graph_uri = named_graph_uri(request.design_space_id)

    # Huidige status ophalen (ondersteunt zowel URI als legacy string-literal)
    rows = await sparql_select(
        f"""SELECT ?status WHERE {{
          <{tessera_uri}> <{VALOR_NS}epistemicStatus> ?status .
        }}""",
        request.design_space_id,
    )

    if not rows:
        raise HTTPException(status_code=404, detail="Tessera niet gevonden in deze DesignSpace.")

    current_raw = rows[0]["status"]
    current_status = _normalize_status(current_raw)

    if request.new_status not in VALID_TRANSITIONS.get(current_status, set()):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Ongeldige transitie: {current_status} → {request.new_status}. "
                f"Toegestaan vanuit '{current_status}': {sorted(VALID_TRANSITIONS.get(current_status, set()))}."
            ),
        )

    if request.new_status in REQUIRES_DECISION_EPISODE and not request.decision_episode_uri:
        raise HTTPException(
            status_code=422,
            detail=f"Status '{request.new_status}' vereist een decision_episode_uri.",
        )

    new_status_uri = EPISTEMIC_STATUS_URIS[request.new_status]

    # Bepaal de waarde om te verwijderen (URI of literal, afhankelijk van wat er staat)
    if current_raw.startswith("http") or current_raw.startswith("urn"):
        old_status_sparql = f"<{current_raw}>"
    else:
        old_status_sparql = f'"{current_raw}"'

    update = f"""DELETE {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> <{VALOR_NS}epistemicStatus> {old_status_sparql} .
  }}
}}
INSERT {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> <{VALOR_NS}epistemicStatus> <{new_status_uri}> .
  }}
}}
WHERE {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> <{VALOR_NS}epistemicStatus> {old_status_sparql} .
  }}
}}"""

    await sparql_update(update, request.design_space_id)

    # Koppel DecisionEpisode indien vereist
    if request.decision_episode_uri:
        episode_update = f"""INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{request.decision_episode_uri}> <{VALOR_NS}concernsTessera> <{tessera_uri}> .
  }}
}}"""
        await sparql_update(episode_update, request.design_space_id)

    logger.info(
        "Tessera %s status: %s → %s (door %s)",
        tessera_uri, current_status, request.new_status, user_id,
    )

    return PatchTesseraStatusResponse(
        tessera_id=tessera_id,
        tessera_uri=tessera_uri,
        previous_status=current_status,
        new_status=request.new_status,
    )


@router.post("/{tessera_id}/evidence", response_model=EvidenceResponse, status_code=201)
async def add_evidence(
    tessera_id: str,
    request: CreateEvidenceRequest,
    user: dict = Depends(get_current_user),
):
    if request.evidence_type not in EVIDENCE_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Ongeldig evidentietype '{request.evidence_type}'. Geldige waarden: {sorted(EVIDENCE_TYPES)}.",
        )

    user_id = user["id"]

    has_permission = await check_permission(user_id, request.design_space_id, Role.MEMBER)
    if not has_permission:
        raise HTTPException(
            status_code=403,
            detail="Onvoldoende rechten voor deze DesignSpace.",
        )

    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    graph_uri = named_graph_uri(request.design_space_id)

    # Controleer of Tessera bestaat
    rows = await sparql_select(
        f"""SELECT ?t WHERE {{
          GRAPH <{graph_uri}> {{
            <{tessera_uri}> a <{VALOR_NS}Tessera> .
            BIND(<{tessera_uri}> AS ?t)
          }}
        }}""",
        request.design_space_id,
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Tessera niet gevonden in deze DesignSpace.")

    evidence_id = str(uuid.uuid4())
    evidence_uri = f"urn:valor:evidence:{evidence_id}"
    user_uri = f"urn:valor:user:{user_id}"
    added_at = datetime.now(timezone.utc).isoformat()

    escaped_strength = request.strength.replace("\\", "\\\\").replace('"', '\\"')
    escaped_source = request.source.replace("\\", "\\\\").replace('"', '\\"')

    sparql = f"""PREFIX valor: <{VALOR_NS}>
PREFIX xsd: <{XSD_NS}>

INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{evidence_uri}> a valor:Evidence ;
      valor:evidenceType "{request.evidence_type}" ;
      valor:strength "{escaped_strength}" ;
      valor:source "{escaped_source}" ;
      valor:addedBy <{user_uri}> ;
      valor:addedAt "{added_at}"^^xsd:dateTime .
    <{tessera_uri}> valor:hasEvidence <{evidence_uri}> .
  }}
}}"""

    await sparql_update(sparql, request.design_space_id)

    logger.info("Evidence %s toegevoegd aan Tessera %s door %s", evidence_uri, tessera_uri, user_id)

    return EvidenceResponse(
        evidence_id=evidence_id,
        evidence_uri=evidence_uri,
        tessera_id=tessera_id,
        tessera_uri=tessera_uri,
        evidence_type=request.evidence_type,
        strength=request.strength,
        source=request.source,
        added_by=user_id,
        added_at=added_at,
    )
