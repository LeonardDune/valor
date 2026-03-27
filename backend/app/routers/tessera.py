import asyncio
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_user
from app.db.permissions import check_permission
from app.models.domain import Role
from app.services.fuseki import sparql_select, sparql_update, sparql_shacl_validate, named_graph_uri, record_provenance_activity
from app.services.ontology_cache import (
    get_evidence_label_to_uri,
    get_status_label_to_uri,
    get_status_uri_to_label,
    get_valid_transitions,
    requires_decision_episode,
    get_argue_label_to_uri,
    get_shacl_shapes_graph,
    get_uncertainty_label_to_uri,
)
from app.ontology import VALOR_NS

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tessera",
    tags=["tessera"],
)

XSD_NS = "http://www.w3.org/2001/XMLSchema#"
CAUSA_NS = f"{VALOR_NS}causa#"


def _normalize_status(raw: str) -> str:
    """Vertaalt een URI naar de canonieke statusnaam (English label)."""
    return get_status_uri_to_label().get(raw, raw)


_CLAIM_TYPE_LABELS = {"AsIs": "AsIsType", "ToBe": "ToBeType"}
_CLAIM_TYPE_SUFFIX_TO_LABEL = {v: k for k, v in _CLAIM_TYPE_LABELS.items()}


def _claim_type_uri(label: str) -> str:
    return f"{VALOR_NS}{_CLAIM_TYPE_LABELS[label]}"


def _claim_type_label_from_raw(raw: str) -> str:
    """Vertaalt URI of string-literal naar de canonieke label ('AsIs'/'ToBe')."""
    if raw.startswith("http") or raw.startswith("urn"):
        suffix = raw.rsplit("/", 1)[-1].rsplit("#", 1)[-1]
        return _CLAIM_TYPE_SUFFIX_TO_LABEL.get(suffix, raw)
    return raw


class CreateTesseraRequest(BaseModel):
    design_space_id: str
    claim_content: str
    claim_type: Optional[str] = "AsIs"  # "AsIs" | "ToBe", default AsIs
    uncertainty_level: Optional[str] = None  # PAMS: "StatisticalRisk" | "Scenario" | "DeepUncertainty" | "Ignorance"
    in_alternative: Optional[str] = None
    in_phase: Optional[str] = None
    manifestation_condition: Optional[str] = None


class TesseraResponse(BaseModel):
    tessera_id: str
    tessera_uri: str
    design_space_id: str
    claim_content: str
    claim_type: str
    epistemic_status: str
    claimed_by: str
    claimed_at: str
    uncertainty_level: Optional[str] = None
    in_alternative: Optional[str] = None
    in_phase: Optional[str] = None
    manifestation_condition: Optional[str] = None
    realised_by: Optional[str] = None


class RealiseRequest(BaseModel):
    design_space_id: str
    transaction_type_uri: str  # URI van het causa:TransactionType


class RealiseResponse(BaseModel):
    tessera_id: str
    tessera_uri: str
    transaction_type_uri: str
    realised_by_uri: str  # de gemaakte causa:realisedBy triple URI (property URI)


class CreateEvidenceRequest(BaseModel):
    design_space_id: str
    evidence_type: str  # English label as defined in ontology (e.g. "Empirical", "Expert Judgement")
    strength: float    # xsd:decimal (0.0–1.0)
    source: str        # URI van het brondocument


class EvidenceResponse(BaseModel):
    evidence_id: str
    evidence_uri: str
    tessera_id: str
    tessera_uri: str
    evidence_type: str
    evidence_type_uri: str
    strength: float
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
    claim_type = request.claim_type or "AsIs"
    if claim_type not in _CLAIM_TYPE_LABELS:
        raise HTTPException(
            status_code=422,
            detail="claim_type moet 'AsIs' of 'ToBe' zijn.",
        )
    claim_type_uri = _claim_type_uri(claim_type)

    uncertainty_level_uri = None
    if request.uncertainty_level:
        uncertainty_label_to_uri = get_uncertainty_label_to_uri()
        uncertainty_level_uri = uncertainty_label_to_uri.get(request.uncertainty_level)
        if not uncertainty_level_uri:
            raise HTTPException(
                status_code=422,
                detail=f"Ongeldig uncertainty_level '{request.uncertainty_level}'. "
                       f"Geldige waarden: {sorted(uncertainty_label_to_uri)}.",
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
    claimed_at = datetime.now(timezone.utc).isoformat()

    # ToBe Tesserae met in_alternative → eigen alternatief-graph
    if claim_type == "ToBe" and request.in_alternative:
        graph_uri = f"urn:valor:ds:{request.design_space_id}/alternative/{request.in_alternative}"
    else:
        graph_uri = named_graph_uri(request.design_space_id)

    status_label_to_uri = get_status_label_to_uri()
    proposed_uri = status_label_to_uri.get("Proposed", f"{VALOR_NS}ProposedStatus")

    optional_triples = ""
    if uncertainty_level_uri:
        optional_triples += f"      <{tessera_uri}> <{VALOR_NS}uncertaintyLevel> <{uncertainty_level_uri}> .\n"
    if request.in_alternative:
        alt_uri = f"urn:valor:alternative:{request.in_alternative}"
        optional_triples += f"      <{tessera_uri}> <{VALOR_NS}inAlternative> <{alt_uri}> .\n"
    if request.in_phase:
        phase_uri = f"urn:valor:phase:{request.in_phase}"
        optional_triples += f"      <{tessera_uri}> <{VALOR_NS}inPhase> <{phase_uri}> .\n"
    if request.manifestation_condition:
        escaped_condition = request.manifestation_condition.replace("\\", "\\\\").replace('"', '\\"')
        optional_triples += f'      <{tessera_uri}> <{CAUSA_NS}hasManifestationCondition> "{escaped_condition}"@nl .\n'

    escaped_content = request.claim_content.replace("\\", "\\\\").replace('"', '\\"')

    sparql = f"""PREFIX valor: <{VALOR_NS}>
PREFIX xsd: <{XSD_NS}>

INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> a valor:Tessera ;
      valor:claimContent "{escaped_content}"@nl ;
      valor:epistemicStatus <{proposed_uri}> ;
      valor:claimType <{claim_type_uri}> ;
      valor:claimedBy <{user_uri}> ;
      valor:claimedAt "{claimed_at}"^^xsd:dateTime ;
      valor:inDesignSpace <{graph_uri}> .
{optional_triples}  }}
}}"""

    await sparql_update(sparql, request.design_space_id)

    asyncio.create_task(record_provenance_activity(
        request.design_space_id,
        "TesseraCreated",
        user_uri,
        generated=tessera_uri,
    ))

    logger.info("Tessera aangemaakt: %s in DesignSpace %s door %s", tessera_uri, request.design_space_id, user_id)

    return TesseraResponse(
        tessera_id=tessera_id,
        tessera_uri=tessera_uri,
        design_space_id=request.design_space_id,
        claim_content=request.claim_content,
        claim_type=claim_type,
        epistemic_status="Proposed",
        claimed_by=user_id,
        claimed_at=claimed_at,
        uncertainty_level=request.uncertainty_level,
        in_alternative=request.in_alternative,
        in_phase=request.in_phase,
        manifestation_condition=request.manifestation_condition,
    )


@router.get("/missing-realisation-basis", response_model=list[TesseraResponse])
async def get_missing_realisation_basis(
    design_space_id: str,
    alternative_id: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """Geeft alle Intervention-Tesserae terug zonder causa:realisedBy koppeling."""
    user_id = user["id"]

    if not await check_permission(user_id, design_space_id, Role.VIEWER):
        raise HTTPException(status_code=403, detail="Onvoldoende rechten voor deze DesignSpace.")

    if alternative_id:
        graph_uri = f"urn:valor:ds:{design_space_id}/alternative/{alternative_id}"
    else:
        graph_uri = named_graph_uri(design_space_id)

    rows = await sparql_select(
        f"""SELECT ?tessera ?content ?claimType ?status ?claimedBy ?claimedAt ?uncertaintyLevel ?inAlternative ?inPhase WHERE {{
          GRAPH <{graph_uri}> {{
            ?tessera a <{VALOR_NS}Tessera> ;
              <{VALOR_NS}claimContent> ?content ;
              <{VALOR_NS}epistemicStatus> ?status ;
              <{VALOR_NS}claimedBy> ?claimedBy ;
              <{VALOR_NS}claimedAt> ?claimedAt .
            OPTIONAL {{ ?tessera <{VALOR_NS}claimType> ?claimType . }}
            OPTIONAL {{ ?tessera <{VALOR_NS}uncertaintyLevel> ?uncertaintyLevel . }}
            OPTIONAL {{ ?tessera <{VALOR_NS}inAlternative> ?inAlternative . }}
            OPTIONAL {{ ?tessera <{VALOR_NS}inPhase> ?inPhase . }}
            FILTER NOT EXISTS {{ ?tessera <{CAUSA_NS}realisedBy> ?any . }}
          }}
        }}""",
        design_space_id,
    )

    uncertainty_label_to_uri = get_uncertainty_label_to_uri()
    uncertainty_uri_to_label = {v: k for k, v in uncertainty_label_to_uri.items()}

    results = []
    for row in rows:
        tessera_uri = row["tessera"]
        tessera_id = tessera_uri.rsplit(":", 1)[-1]
        raw_claim_type = row.get("claimType", "")
        claim_type = _claim_type_label_from_raw(raw_claim_type) if raw_claim_type else "AsIs"
        raw_uncertainty = row.get("uncertaintyLevel", "")
        uncertainty_level = uncertainty_uri_to_label.get(raw_uncertainty) if raw_uncertainty else None
        results.append(TesseraResponse(
            tessera_id=tessera_id,
            tessera_uri=tessera_uri,
            design_space_id=design_space_id,
            claim_content=row["content"],
            claim_type=claim_type,
            epistemic_status=_normalize_status(row["status"]),
            claimed_by=row["claimedBy"].rsplit(":", 1)[-1],
            claimed_at=row["claimedAt"],
            uncertainty_level=uncertainty_level,
            in_alternative=row.get("inAlternative"),
            in_phase=row.get("inPhase"),
            realised_by=None,
        ))

    return results


@router.get("/{tessera_id}", response_model=TesseraResponse)
async def get_tessera(
    tessera_id: str,
    design_space_id: str,
    alternative_id: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    user_id = user["id"]

    if not await check_permission(user_id, design_space_id, Role.VIEWER):
        raise HTTPException(status_code=403, detail="Onvoldoende rechten voor deze DesignSpace.")

    tessera_uri = f"urn:valor:tessera:{tessera_id}"

    if alternative_id:
        graph_uri = f"urn:valor:ds:{design_space_id}/alternative/{alternative_id}"
    else:
        graph_uri = named_graph_uri(design_space_id)

    rows = await sparql_select(
        f"""SELECT ?content ?claimType ?uncertaintyLevel ?status ?claimedBy ?claimedAt ?inAlternative ?inPhase ?manifestationCondition ?realisedBy WHERE {{
          GRAPH <{graph_uri}> {{
            <{tessera_uri}> a <{VALOR_NS}Tessera> ;
              <{VALOR_NS}claimContent> ?content ;
              <{VALOR_NS}epistemicStatus> ?status ;
              <{VALOR_NS}claimedBy> ?claimedBy ;
              <{VALOR_NS}claimedAt> ?claimedAt .
            OPTIONAL {{ <{tessera_uri}> <{VALOR_NS}claimType> ?claimType . }}
            OPTIONAL {{ <{tessera_uri}> <{VALOR_NS}uncertaintyLevel> ?uncertaintyLevel . }}
            OPTIONAL {{ <{tessera_uri}> <{VALOR_NS}inAlternative> ?inAlternative . }}
            OPTIONAL {{ <{tessera_uri}> <{VALOR_NS}inPhase> ?inPhase . }}
            OPTIONAL {{ <{tessera_uri}> <{CAUSA_NS}hasManifestationCondition> ?manifestationCondition . }}
            OPTIONAL {{ <{tessera_uri}> <{CAUSA_NS}realisedBy> ?realisedBy . }}
          }}
        }}""",
        design_space_id,
    )

    if not rows:
        raise HTTPException(status_code=404, detail="Tessera niet gevonden in deze DesignSpace.")

    row = rows[0]
    raw_claim_type = row.get("claimType", "")
    claim_type = _claim_type_label_from_raw(raw_claim_type) if raw_claim_type else "AsIs"

    raw_uncertainty = row.get("uncertaintyLevel", "")
    uncertainty_label_to_uri = get_uncertainty_label_to_uri()
    uncertainty_uri_to_label = {v: k for k, v in uncertainty_label_to_uri.items()}
    uncertainty_level = uncertainty_uri_to_label.get(raw_uncertainty) if raw_uncertainty else None

    return TesseraResponse(
        tessera_id=tessera_id,
        tessera_uri=tessera_uri,
        design_space_id=design_space_id,
        claim_content=row["content"],
        claim_type=claim_type,
        epistemic_status=_normalize_status(row["status"]),
        claimed_by=row["claimedBy"].rsplit(":", 1)[-1],
        claimed_at=row["claimedAt"],
        uncertainty_level=uncertainty_level,
        in_alternative=row.get("inAlternative"),
        in_phase=row.get("inPhase"),
        manifestation_condition=row.get("manifestationCondition"),
        realised_by=row.get("realisedBy"),
    )


@router.post("/{tessera_id}/realise", response_model=RealiseResponse, status_code=201)
async def realise_tessera(
    tessera_id: str,
    request: RealiseRequest,
    user: dict = Depends(get_current_user),
):
    """Koppelt een Intervention-Tessera aan een causa:TransactionType via causa:realisedBy."""
    user_id = user["id"]

    if not await check_permission(user_id, request.design_space_id, Role.MEMBER):
        raise HTTPException(status_code=403, detail="Onvoldoende rechten voor deze DesignSpace.")

    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    graph_uri = named_graph_uri(request.design_space_id)

    # Controleer dat de Tessera bestaat
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

    # Idempotent: verwijder eventuele bestaande realisedBy koppeling en schrijf de nieuwe
    escaped_transaction_uri = request.transaction_type_uri.replace("\\", "\\\\").replace('"', '\\"')

    update = f"""DELETE {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> <{CAUSA_NS}realisedBy> ?prev .
  }}
}}
INSERT {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> <{CAUSA_NS}realisedBy> <{escaped_transaction_uri}> .
  }}
}}
WHERE {{
  GRAPH <{graph_uri}> {{
    OPTIONAL {{ <{tessera_uri}> <{CAUSA_NS}realisedBy> ?prev . }}
  }}
}}"""

    await sparql_update(update, request.design_space_id)

    asyncio.create_task(record_provenance_activity(
        request.design_space_id,
        "RealisedByLinked",
        f"urn:valor:user:{user_id}",
        used=[tessera_uri],
        extra_props=[(f"{CAUSA_NS}realisedBy", request.transaction_type_uri)],
    ))

    logger.info(
        "Tessera %s gekoppeld aan TransactionType %s door %s",
        tessera_uri, request.transaction_type_uri, user_id,
    )

    return RealiseResponse(
        tessera_id=tessera_id,
        tessera_uri=tessera_uri,
        transaction_type_uri=request.transaction_type_uri,
        realised_by_uri=f"{CAUSA_NS}realisedBy",
    )


@router.patch("/{tessera_id}/status", response_model=PatchTesseraStatusResponse)
async def patch_tessera_status(
    tessera_id: str,
    request: PatchTesseraStatusRequest,
    user: dict = Depends(get_current_user),
):
    valid_transitions = get_valid_transitions()
    if request.new_status not in valid_transitions:
        raise HTTPException(
            status_code=422,
            detail=f"Ongeldig doelstatus '{request.new_status}'. Geldige waarden: {sorted(valid_transitions)}.",
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

    if request.new_status not in valid_transitions.get(current_status, set()):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Ongeldige transitie: {current_status} → {request.new_status}. "
                f"Toegestaan vanuit '{current_status}': {sorted(valid_transitions.get(current_status, set()))}."
            ),
        )

    status_label_to_uri = get_status_label_to_uri()
    new_status_uri = status_label_to_uri.get(request.new_status)
    if not new_status_uri:
        raise HTTPException(status_code=422, detail=f"Status '{request.new_status}' niet gevonden in ontologie.")

    if requires_decision_episode(new_status_uri) and not request.decision_episode_uri:
        raise HTTPException(
            status_code=422,
            detail=f"Status '{request.new_status}' vereist een decision_episode_uri.",
        )

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

    if request.decision_episode_uri:
        episode_update = f"""INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{request.decision_episode_uri}> <{VALOR_NS}concernsTessera> <{tessera_uri}> .
  }}
}}"""
        await sparql_update(episode_update, request.design_space_id)

    status_label_to_uri_map = get_status_label_to_uri()
    old_status_uri = status_label_to_uri_map.get(current_status, current_raw)
    asyncio.create_task(record_provenance_activity(
        request.design_space_id,
        "StatusChanged",
        f"urn:valor:user:{user_id}",
        used=[tessera_uri],
        extra_props=[
            (f"{VALOR_NS}previousStatus", old_status_uri),
            (f"{VALOR_NS}newStatus", new_status_uri),
        ],
    ))

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
    evidence_label_to_uri = get_evidence_label_to_uri()
    evidence_type_uri = evidence_label_to_uri.get(request.evidence_type)
    if not evidence_type_uri:
        raise HTTPException(
            status_code=422,
            detail=f"Ongeldig evidentietype '{request.evidence_type}'. Geldige waarden: {sorted(evidence_label_to_uri)}.",
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

    escaped_source = request.source.replace("\\", "\\\\").replace('"', '\\"')

    sparql = f"""PREFIX valor: <{VALOR_NS}>
PREFIX xsd: <{XSD_NS}>

INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{evidence_uri}> a valor:Evidence ;
      valor:evidenceType <{evidence_type_uri}> ;
      valor:evidenceStrength "{request.strength}"^^xsd:decimal ;
      valor:evidenceSource "{escaped_source}"^^xsd:anyURI ;
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
        evidence_type_uri=evidence_type_uri,
        strength=request.strength,
        source=request.source,
        added_by=user_id,
        added_at=added_at,
    )


class CreateArgueRequest(BaseModel):
    design_space_id: str
    relation_type: str   # English label: "supports" | "undermines" | "qualifies" | "presupposes"
    target_tessera_id: str


class ArgueResponse(BaseModel):
    relation_uri: str
    source_tessera_id: str
    source_tessera_uri: str
    target_tessera_id: str
    target_tessera_uri: str
    relation_type: str
    relation_type_uri: str
    contested_triggered: bool  # true als undermines de target naar Contested bracht


@router.post("/{tessera_id}/argue", response_model=ArgueResponse, status_code=201)
async def argue(
    tessera_id: str,
    request: CreateArgueRequest,
    user: dict = Depends(get_current_user),
):
    argue_label_to_uri = get_argue_label_to_uri()
    relation_uri = argue_label_to_uri.get(request.relation_type)
    if not relation_uri:
        raise HTTPException(
            status_code=422,
            detail=f"Ongeldig relatietype '{request.relation_type}'. Geldige waarden: {sorted(argue_label_to_uri)}.",
        )

    user_id = user["id"]

    has_permission = await check_permission(user_id, request.design_space_id, Role.MEMBER)
    if not has_permission:
        raise HTTPException(
            status_code=403,
            detail="Onvoldoende rechten voor deze DesignSpace.",
        )

    source_uri = f"urn:valor:tessera:{tessera_id}"
    target_uri = f"urn:valor:tessera:{request.target_tessera_id}"
    graph_uri = named_graph_uri(request.design_space_id)

    # Controleer beide Tesserae
    rows = await sparql_select(
        f"""SELECT ?t WHERE {{
          GRAPH <{graph_uri}> {{
            VALUES ?t {{ <{source_uri}> <{target_uri}> }}
            ?t a <{VALOR_NS}Tessera> .
          }}
        }}""",
        request.design_space_id,
    )
    found = {r["t"] for r in rows}
    if source_uri not in found:
        raise HTTPException(status_code=404, detail="Bron-Tessera niet gevonden in deze DesignSpace.")
    if target_uri not in found:
        raise HTTPException(status_code=404, detail="Doel-Tessera niet gevonden in deze DesignSpace.")

    # INSERT de argumentatierelatie
    await sparql_update(
        f"""INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{source_uri}> <{relation_uri}> <{target_uri}> .
  }}
}}""",
        request.design_space_id,
    )

    # SHACL-validatie via Fuseki — rollback bij violations (o.a. T5: non-reflexive undermines)
    violations = await sparql_shacl_validate(request.design_space_id, get_shacl_shapes_graph())
    if violations:
        await sparql_update(
            f"""DELETE DATA {{
  GRAPH <{graph_uri}> {{
    <{source_uri}> <{relation_uri}> <{target_uri}> .
  }}
}}""",
            request.design_space_id,
        )
        raise HTTPException(
            status_code=422,
            detail={"message": "SHACL-validatie mislukt.", "violations": violations},
        )

    # undermines → target-Tessera naar Contested als die Proposed is (DD-065 §B)
    contested_triggered = False
    undermines_uri = argue_label_to_uri.get("undermines")
    if relation_uri == undermines_uri:
        status_rows = await sparql_select(
            f"""SELECT ?status WHERE {{
              <{target_uri}> <{VALOR_NS}epistemicStatus> ?status .
            }}""",
            request.design_space_id,
        )
        if status_rows:
            current_uri = status_rows[0]["status"]
            current_label = get_status_uri_to_label().get(current_uri, "")
            if current_label == "Proposed":
                contested_uri = get_status_label_to_uri().get("Contested")
                if contested_uri:
                    await sparql_update(
                        f"""DELETE {{
  GRAPH <{graph_uri}> {{
    <{target_uri}> <{VALOR_NS}epistemicStatus> <{current_uri}> .
  }}
}}
INSERT {{
  GRAPH <{graph_uri}> {{
    <{target_uri}> <{VALOR_NS}epistemicStatus> <{contested_uri}> .
  }}
}}
WHERE {{
  GRAPH <{graph_uri}> {{
    <{target_uri}> <{VALOR_NS}epistemicStatus> <{current_uri}> .
  }}
}}""",
                        request.design_space_id,
                    )
                    contested_triggered = True
                    logger.info("Tessera %s naar Contested door undermines van %s", target_uri, source_uri)

    asyncio.create_task(record_provenance_activity(
        request.design_space_id,
        "ArgumentAdded",
        f"urn:valor:user:{user_id}",
        used=[source_uri, target_uri],
        extra_props=[(relation_uri, target_uri)],
    ))

    logger.info(
        "Argumentatierelatie: %s -[%s]-> %s (door %s)",
        source_uri, request.relation_type, target_uri, user_id,
    )

    return ArgueResponse(
        relation_uri=relation_uri,
        source_tessera_id=tessera_id,
        source_tessera_uri=source_uri,
        target_tessera_id=request.target_tessera_id,
        target_tessera_uri=target_uri,
        relation_type=request.relation_type,
        relation_type_uri=relation_uri,
        contested_triggered=contested_triggered,
    )


class ProvenanceActivity(BaseModel):
    activity_uri: str
    operation_type: str
    attributed_to: str
    started_at: str
    generated: Optional[str] = None
    used: list[str] = []


@router.get("/{tessera_id}/provenance", response_model=list[ProvenanceActivity])
async def get_tessera_provenance(
    tessera_id: str,
    design_space_id: str,
    user: dict = Depends(get_current_user),
):
    """Geeft de PROV-O provenance-keten terug voor een Tessera."""
    user_id = user["id"]

    if not await check_permission(user_id, design_space_id, Role.VIEWER):
        raise HTTPException(status_code=403, detail="Onvoldoende rechten voor deze DesignSpace.")

    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    prov_graph = f"urn:valor:ds:{design_space_id}/provenance"
    PROV_NS = "https://www.w3.org/ns/prov#"

    rows = await sparql_select(
        f"""PREFIX prov: <{PROV_NS}>
SELECT ?activity ?opType ?agent ?startedAt ?generated WHERE {{
  GRAPH <{prov_graph}> {{
    ?activity a prov:Activity ;
      <urn:valor:operationType> ?opType ;
      prov:wasAttributedTo ?agent ;
      prov:startedAtTime ?startedAt .
    OPTIONAL {{ ?activity prov:generated ?generated . }}
    FILTER(
      ?activity = ?activity &&
      (
        EXISTS {{ ?activity prov:generated <{tessera_uri}> . }}
        || EXISTS {{ ?activity prov:used <{tessera_uri}> . }}
      )
    )
  }}
}}
ORDER BY ?startedAt""",
        design_space_id,
    )

    # Haal ook `used` op per activity
    used_rows = await sparql_select(
        f"""PREFIX prov: <{PROV_NS}>
SELECT ?activity ?used WHERE {{
  GRAPH <{prov_graph}> {{
    ?activity a prov:Activity ;
      prov:used ?used .
    FILTER(
      EXISTS {{ ?activity prov:generated <{tessera_uri}> . }}
      || ?used = <{tessera_uri}>
    )
  }}
}}""",
        design_space_id,
    )

    used_by_activity: dict[str, list[str]] = {}
    for r in used_rows:
        used_by_activity.setdefault(r["activity"], []).append(r["used"])

    results = []
    for row in rows:
        activity_uri = row["activity"]
        op_uri = row["opType"]
        op_label = op_uri.rsplit(":", 1)[-1]
        agent = row["agent"].rsplit(":", 1)[-1]
        results.append(ProvenanceActivity(
            activity_uri=activity_uri,
            operation_type=op_label,
            attributed_to=agent,
            started_at=row["startedAt"],
            generated=row.get("generated"),
            used=used_by_activity.get(activity_uri, []),
        ))

    return results
