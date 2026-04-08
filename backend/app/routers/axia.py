import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_user
from app.db.permissions import check_permission
from app.models.domain import Role
from app.services.fuseki import sparql_select_global, sparql_update, record_provenance_activity
from app.services.ontology_cache import get_status_label_to_uri
from app.ontology import VALOR_NS

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/designspace",
    tags=["axia"],
)

AXIA_NS = "https://valor-ecosystem.nl/ontology/axia#"
CAPAX_NS = "https://valor-ecosystem.nl/ontology/capax#"
COVER_NS = "https://valor-ecosystem.nl/ontology/cover#"
XSD_NS = "http://www.w3.org/2001/XMLSchema#"


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ValueClaimOut(BaseModel):
    tessera_uri: str
    tessera_id: str
    claim_content: str
    value_type_uri: str
    value_type_label: str
    polarity_uri: str | None = None
    polarity_label: str | None = None
    epistemic_status: str | None = None
    canvas_x: float | None = None
    canvas_y: float | None = None
    claimed_by: str
    claimed_at: str


class ValueCanvasOut(BaseModel):
    design_space_id: str
    groups: dict[str, list[ValueClaimOut]]


class UpdateValueClaimRequest(BaseModel):
    claim_content: str | None = None
    value_type_uri: str | None = None


class CreateValueTensionRequest(BaseModel):
    value_type_a_uri: str
    value_type_b_uri: str
    description: str


class ValueTensionOut(BaseModel):
    tessera_uri: str
    tessera_id: str
    value_type_a_uri: str
    value_type_b_uri: str
    description: str
    created_by: str
    created_at: str


# ---------------------------------------------------------------------------
# US-7.1: GET value-claims gegroepeerd per ValueType
# ---------------------------------------------------------------------------

@router.get("/{ds_id}/value-claims", response_model=ValueCanvasOut)
async def get_value_claims(
    ds_id: str,
    user: dict = Depends(get_current_user),
) -> ValueCanvasOut:
    user_id = user["id"]

    has_permission = await check_permission(user_id, ds_id, Role.VIEWER)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Onvoldoende rechten voor deze DesignSpace.")

    graph_uri = f"urn:valor:ds:{ds_id}/baseline"

    query = f"""PREFIX axia: <{AXIA_NS}>
PREFIX cover: <{COVER_NS}>
PREFIX valor: <{VALOR_NS}>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?tessera ?content ?valueType ?valueTypeLabel ?polarity ?polarityLabel ?status ?cx ?cy ?claimedBy ?claimedAt WHERE {{
  GRAPH <{graph_uri}> {{
    ?tessera a axia:ValueClaim ;
             valor:claimContent ?content ;
             valor:claimedBy ?claimedBy ;
             valor:claimedAt ?claimedAt .
    FILTER NOT EXISTS {{ ?tessera valor:retiredAt ?t . }}
    OPTIONAL {{
      ?tessera axia:concernsValueType ?valueType .
      FILTER(STRSTARTS(STR(?valueType), "https://"))
    }}
    OPTIONAL {{ ?valueType rdfs:label ?valueTypeLabel . }}
    OPTIONAL {{ ?tessera axia:claimPolarity ?polarity . }}
    OPTIONAL {{ ?polarity rdfs:label ?polarityLabel . }}
    OPTIONAL {{ ?tessera valor:epistemicStatus ?status . }}
    OPTIONAL {{ ?tessera valor:canvasX ?cx . }}
    OPTIONAL {{ ?tessera valor:canvasY ?cy . }}
  }}
}}
ORDER BY ?valueType"""

    rows = await sparql_select_global(query)

    # Dedupliceer: houd per tessera_uri alleen de eerste rij (bescherming tegen meerdere valueType-triples)
    seen_tesserae: set[str] = set()
    deduped: list[dict] = []
    for row in rows:
        uri = row.get("tessera", "")
        if uri not in seen_tesserae:
            seen_tesserae.add(uri)
            deduped.append(row)
    rows = deduped

    groups: dict[str, list[ValueClaimOut]] = {}
    for row in rows:
        tessera_uri = row.get("tessera", "")
        tessera_id = tessera_uri.rsplit(":", 1)[-1]
        value_type_uri = row.get("valueType", "")
        value_type_label = row.get("valueTypeLabel", value_type_uri.rsplit("#", 1)[-1] if "#" in value_type_uri else value_type_uri.rsplit("/", 1)[-1])
        polarity_uri = row.get("polarity") or None
        polarity_label_raw = row.get("polarityLabel") or None
        status_raw = row.get("status") or None
        status_label = status_raw.rsplit("#", 1)[-1].rsplit("/", 1)[-1] if status_raw else None
        cx_raw = row.get("cx")
        cy_raw = row.get("cy")

        claim = ValueClaimOut(
            tessera_uri=tessera_uri,
            tessera_id=tessera_id,
            claim_content=row.get("content", ""),
            value_type_uri=value_type_uri,
            value_type_label=value_type_label,
            polarity_uri=polarity_uri,
            polarity_label=polarity_label_raw,
            epistemic_status=status_label,
            canvas_x=float(cx_raw) if cx_raw is not None else None,
            canvas_y=float(cy_raw) if cy_raw is not None else None,
            claimed_by=row.get("claimedBy", "").rsplit(":", 1)[-1],
            claimed_at=row.get("claimedAt", ""),
        )

        groups.setdefault(value_type_uri, []).append(claim)

    return ValueCanvasOut(design_space_id=ds_id, groups=groups)


# ---------------------------------------------------------------------------
# US-7.1: POST value-claim
# ---------------------------------------------------------------------------

class CreateValueClaimRequest(BaseModel):
    claim_content: str
    value_type_uri: str | None = None      # volledige URI, bijv. https://valor-ecosystem.nl/ontology/cover#FairnessExperience
    claim_polarity_uri: str | None = None  # volledige URI, bijv. https://valor-ecosystem.nl/ontology/axia#SupportingPolarity


class ValueClaimCreatedOut(BaseModel):
    tessera_uri: str
    tessera_id: str
    claim_content: str
    value_type_uri: str | None
    claimed_by: str
    claimed_at: str


@router.post("/{ds_id}/value-claim", response_model=ValueClaimCreatedOut, status_code=201)
async def create_value_claim(
    ds_id: str,
    request: CreateValueClaimRequest,
    user: dict = Depends(get_current_user),
) -> ValueClaimCreatedOut:
    user_id = user["id"]

    has_permission = await check_permission(user_id, ds_id, Role.MEMBER)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Onvoldoende rechten voor deze DesignSpace.")

    tessera_id = str(uuid.uuid4())
    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    user_uri = f"urn:valor:user:{user_id}"
    created_at = datetime.now(timezone.utc).isoformat()
    graph_uri = f"urn:valor:ds:{ds_id}/baseline"

    escaped_content = request.claim_content.replace("\\", "\\\\").replace('"', '\\"')

    value_type_triple = ""
    if request.value_type_uri:
        value_type_triple = f'\n      axia:concernsValueType <{request.value_type_uri}> ;'

    polarity_triple = ""
    if request.claim_polarity_uri:
        polarity_triple = f'\n      axia:claimPolarity <{request.claim_polarity_uri}> ;'

    sparql = f"""PREFIX axia: <{AXIA_NS}>
PREFIX valor: <{VALOR_NS}>
PREFIX xsd: <{XSD_NS}>

INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> a axia:ValueClaim ;
      a valor:Tessera ;
      valor:claimContent "{escaped_content}"@nl ;{value_type_triple}{polarity_triple}
      valor:epistemicStatus <{VALOR_NS}ProposedStatus> ;
      valor:claimType <{VALOR_NS}ToBeType> ;
      valor:claimedBy <{user_uri}> ;
      valor:claimedAt "{created_at}"^^xsd:dateTime .
  }}
}}"""

    await sparql_update(sparql, ds_id)

    await record_provenance_activity(
        ds_id,
        "ValueClaimCreated",
        user_uri,
        generated=tessera_uri,
    )

    logger.info("ValueClaim aangemaakt: %s in DesignSpace %s door %s", tessera_uri, ds_id, user_id)

    return ValueClaimCreatedOut(
        tessera_uri=tessera_uri,
        tessera_id=tessera_id,
        claim_content=request.claim_content,
        value_type_uri=request.value_type_uri,
        claimed_by=user_id,
        claimed_at=created_at,
    )


# ---------------------------------------------------------------------------
# US-7.2: PATCH value-claim position (canvas) — MOET voor de algemene PATCH staan
# ---------------------------------------------------------------------------

class UpdateValueClaimPositionRequest(BaseModel):
    canvas_x: float
    canvas_y: float


@router.patch("/{ds_id}/value-claim/{tessera_id}/position", status_code=200)
async def update_value_claim_position(
    ds_id: str,
    tessera_id: str,
    request: UpdateValueClaimPositionRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    user_id = user["id"]

    has_permission = await check_permission(user_id, ds_id, Role.MEMBER)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Onvoldoende rechten voor deze DesignSpace.")

    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    graph_uri = f"urn:valor:ds:{ds_id}/baseline"

    sparql = f"""PREFIX valor: <{VALOR_NS}>
PREFIX xsd: <{XSD_NS}>

DELETE {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> valor:canvasX ?oldX ;
                    valor:canvasY ?oldY .
  }}
}}
INSERT {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> valor:canvasX "{request.canvas_x}"^^xsd:decimal ;
                    valor:canvasY "{request.canvas_y}"^^xsd:decimal .
  }}
}}
WHERE {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> a valor:Tessera .
    OPTIONAL {{ <{tessera_uri}> valor:canvasX ?oldX . }}
    OPTIONAL {{ <{tessera_uri}> valor:canvasY ?oldY . }}
  }}
}}"""

    await sparql_update(sparql, ds_id)
    return {"tessera_uri": tessera_uri, "canvas_x": request.canvas_x, "canvas_y": request.canvas_y}


# ---------------------------------------------------------------------------
# PATCH / DELETE value-claim
# ---------------------------------------------------------------------------

@router.patch("/{ds_id}/value-claim/{tessera_uri:path}", status_code=200)
async def update_value_claim(
    ds_id: str,
    tessera_uri: str,
    request: UpdateValueClaimRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    user_id = user["id"]

    has_permission = await check_permission(user_id, ds_id, Role.MEMBER)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Onvoldoende rechten voor deze DesignSpace.")

    if request.claim_content is None and request.value_type_uri is None:
        raise HTTPException(status_code=422, detail="Minimaal claim_content of value_type_uri is vereist.")

    graph_uri = f"urn:valor:ds:{ds_id}/baseline"

    delete_parts = []
    insert_parts = []

    if request.claim_content is not None:
        escaped = request.claim_content.replace("\\", "\\\\").replace('"', '\\"')
        delete_parts.append(f'    <{tessera_uri}> valor:claimContent ?oldContent .')
        insert_parts.append(f'    <{tessera_uri}> valor:claimContent "{escaped}"@nl .')

    if request.value_type_uri is not None:
        delete_parts.append(f'    <{tessera_uri}> axia:concernsValueType ?oldType .')
        insert_parts.append(f'    <{tessera_uri}> axia:concernsValueType <{request.value_type_uri}> .')

    delete_block = "\n".join(delete_parts)
    insert_block = "\n".join(insert_parts)

    sparql = f"""PREFIX axia: <{AXIA_NS}>
PREFIX valor: <{VALOR_NS}>

DELETE {{
  GRAPH <{graph_uri}> {{
{delete_block}
  }}
}}
INSERT {{
  GRAPH <{graph_uri}> {{
{insert_block}
  }}
}}
WHERE {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> a axia:ValueClaim .
    OPTIONAL {{ <{tessera_uri}> valor:claimContent ?oldContent . }}
    OPTIONAL {{ <{tessera_uri}> axia:concernsValueType ?oldType . }}
  }}
}}"""

    await sparql_update(sparql, ds_id)

    user_uri = f"urn:valor:user:{user_id}"
    await record_provenance_activity(ds_id, "ValueClaimUpdated", user_uri, used=[tessera_uri])

    logger.info("ValueClaim bijgewerkt: %s in DesignSpace %s door %s", tessera_uri, ds_id, user_id)

    return {"tessera_uri": tessera_uri, "updated": True}


@router.delete("/{ds_id}/value-claim/{tessera_uri:path}", status_code=200)
async def delete_value_claim(
    ds_id: str,
    tessera_uri: str,
    user: dict = Depends(get_current_user),
) -> dict:
    user_id = user["id"]

    has_permission = await check_permission(user_id, ds_id, Role.MEMBER)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Onvoldoende rechten voor deze DesignSpace.")

    graph_uri = f"urn:valor:ds:{ds_id}/baseline"

    sparql = f"""DELETE WHERE {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> ?p ?o .
  }}
}}"""

    await sparql_update(sparql, ds_id)

    user_uri = f"urn:valor:user:{user_id}"
    await record_provenance_activity(ds_id, "ValueClaimDeleted", user_uri, used=[tessera_uri])

    logger.info("ValueClaim verwijderd: %s uit DesignSpace %s door %s", tessera_uri, ds_id, user_id)

    return {"status": "deleted", "tessera_uri": tessera_uri}


# ---------------------------------------------------------------------------
# US-7.2: POST value-tension
# ---------------------------------------------------------------------------

@router.post("/{ds_id}/value-tension", response_model=ValueTensionOut, status_code=201)
async def create_value_tension(
    ds_id: str,
    request: CreateValueTensionRequest,
    user: dict = Depends(get_current_user),
) -> ValueTensionOut:
    user_id = user["id"]

    has_permission = await check_permission(user_id, ds_id, Role.MEMBER)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Onvoldoende rechten voor deze DesignSpace.")

    tessera_id = str(uuid.uuid4())
    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    user_uri = f"urn:valor:user:{user_id}"
    created_at = datetime.now(timezone.utc).isoformat()
    graph_uri = f"urn:valor:ds:{ds_id}/baseline"

    escaped_desc = request.description.replace("\\", "\\\\").replace('"', '\\"')

    sparql = f"""PREFIX axia: <{AXIA_NS}>
PREFIX cover: <{COVER_NS}>
PREFIX valor: <{VALOR_NS}>
PREFIX xsd: <{XSD_NS}>

INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> a axia:ValueTensionClaim ;
      a valor:Tessera ;
      valor:claimContent "{escaped_desc}"@nl ;
      axia:tensionBetween <{request.value_type_a_uri}> ;
      axia:tensionBetween <{request.value_type_b_uri}> ;
      axia:spanningWaarde <{request.value_type_a_uri}> ;
      axia:spanningWaarde <{request.value_type_b_uri}> ;
      valor:claimedBy <{user_uri}> ;
      valor:claimedAt "{created_at}"^^xsd:dateTime .
  }}
}}"""

    await sparql_update(sparql, ds_id)

    await record_provenance_activity(
        ds_id,
        "ValueTensionCreated",
        user_uri,
        generated=tessera_uri,
    )

    logger.info("ValueTensionClaim aangemaakt: %s in DesignSpace %s door %s", tessera_uri, ds_id, user_id)

    return ValueTensionOut(
        tessera_uri=tessera_uri,
        tessera_id=tessera_id,
        value_type_a_uri=request.value_type_a_uri,
        value_type_b_uri=request.value_type_b_uri,
        description=request.description,
        created_by=user_id,
        created_at=created_at,
    )


# ---------------------------------------------------------------------------
# US-7.3: GET value-implications per factor
# ---------------------------------------------------------------------------

class CreateValueCriterionRequest(BaseModel):
    label: str
    value_type_uri: str
    grounded_in_norm_uri: str | None = None


class ValueCriterionOut(BaseModel):
    tessera_uri: str
    tessera_id: str
    label: str
    value_type_uri: str
    grounded_in_norm_uri: str | None
    created_by: str
    created_at: str


class CreateValueBasedDesignRequirementRequest(BaseModel):
    label: str
    criterion_uri: str


class ValueBasedDesignRequirementOut(BaseModel):
    tessera_uri: str
    tessera_id: str
    label: str
    criterion_uri: str
    created_by: str
    created_at: str


class ValueChainRequirementItem(BaseModel):
    tessera_uri: str
    tessera_id: str
    label: str
    epistemic_status: str | None = None
    capability_requirement_uri: str | None = None


class ValueChainCriterionItem(BaseModel):
    tessera_uri: str
    tessera_id: str
    label: str
    requirements: list[ValueChainRequirementItem]


class ValueChainTypeItem(BaseModel):
    value_type_uri: str
    value_type_label: str
    criteria: list[ValueChainCriterionItem]


class ValueChainOut(BaseModel):
    design_space_id: str
    chain: list[ValueChainTypeItem]


class DesignImplicationCount(BaseModel):
    factor_uri: str
    implication_count: int


@router.get("/{ds_id}/value-implications", response_model=list[DesignImplicationCount])
async def get_value_implications(
    ds_id: str,
    user: dict = Depends(get_current_user),
) -> list[DesignImplicationCount]:
    user_id = user["id"]

    has_permission = await check_permission(user_id, ds_id, Role.VIEWER)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Onvoldoende rechten voor deze DesignSpace.")

    graph_uri = f"urn:valor:ds:{ds_id}/baseline"

    query = f"""PREFIX axia: <{AXIA_NS}>

SELECT ?factor (COUNT(?implication) AS ?count) WHERE {{
  GRAPH <{graph_uri}> {{
    ?implication a axia:DesignImplication ;
                 axia:impliesFor ?factor .
  }}
}}
GROUP BY ?factor
ORDER BY DESC(?count)"""

    rows = await sparql_select_global(query)

    return [
        DesignImplicationCount(
            factor_uri=row["factor"],
            implication_count=int(row["count"]),
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# US-7.4: POST value-criterion
# ---------------------------------------------------------------------------

@router.post("/{ds_id}/value-criterion", response_model=ValueCriterionOut, status_code=201)
async def create_value_criterion(
    ds_id: str,
    request: CreateValueCriterionRequest,
    user: dict = Depends(get_current_user),
) -> ValueCriterionOut:
    user_id = user["id"]

    has_permission = await check_permission(user_id, ds_id, Role.MEMBER)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Onvoldoende rechten voor deze DesignSpace.")

    tessera_id = str(uuid.uuid4())
    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    user_uri = f"urn:valor:user:{user_id}"
    created_at = datetime.now(timezone.utc).isoformat()
    graph_uri = f"urn:valor:ds:{ds_id}/baseline"

    escaped_label = request.label.replace("\\", "\\\\").replace('"', '\\"')

    norm_triple = ""
    if request.grounded_in_norm_uri:
        norm_triple = f'\n      cover:groundedIn <{request.grounded_in_norm_uri}> ;'

    sparql = f"""PREFIX axia: <{AXIA_NS}>
PREFIX cover: <{COVER_NS}>
PREFIX valor: <{VALOR_NS}>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <{XSD_NS}>

INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> a axia:ValueCriterion ;
      a valor:Tessera ;
      rdfs:label "{escaped_label}"@nl ;
      cover:groundedIn <{request.value_type_uri}> ;{norm_triple}
      valor:claimedBy <{user_uri}> ;
      valor:claimedAt "{created_at}"^^xsd:dateTime .
  }}
}}"""

    await sparql_update(sparql, ds_id)

    await record_provenance_activity(
        ds_id,
        "ValueCriterionCreated",
        user_uri,
        generated=tessera_uri,
    )

    logger.info("ValueCriterion aangemaakt: %s in DesignSpace %s door %s", tessera_uri, ds_id, user_id)

    return ValueCriterionOut(
        tessera_uri=tessera_uri,
        tessera_id=tessera_id,
        label=request.label,
        value_type_uri=request.value_type_uri,
        grounded_in_norm_uri=request.grounded_in_norm_uri,
        created_by=user_id,
        created_at=created_at,
    )


# ---------------------------------------------------------------------------
# US-7.4: POST value-based-design-requirement
# ---------------------------------------------------------------------------

@router.post("/{ds_id}/value-based-design-requirement", response_model=ValueBasedDesignRequirementOut, status_code=201)
async def create_value_based_design_requirement(
    ds_id: str,
    request: CreateValueBasedDesignRequirementRequest,
    user: dict = Depends(get_current_user),
) -> ValueBasedDesignRequirementOut:
    user_id = user["id"]

    has_permission = await check_permission(user_id, ds_id, Role.MEMBER)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Onvoldoende rechten voor deze DesignSpace.")

    tessera_id = str(uuid.uuid4())
    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    user_uri = f"urn:valor:user:{user_id}"
    created_at = datetime.now(timezone.utc).isoformat()
    graph_uri = f"urn:valor:ds:{ds_id}/baseline"

    escaped_label = request.label.replace("\\", "\\\\").replace('"', '\\"')

    sparql = f"""PREFIX axia: <{AXIA_NS}>
PREFIX valor: <{VALOR_NS}>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <{XSD_NS}>

INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> a axia:ValueBasedDesignRequirement ;
      a valor:Tessera ;
      rdfs:label "{escaped_label}"@nl ;
      valor:claimedBy <{user_uri}> ;
      valor:claimedAt "{created_at}"^^xsd:dateTime .
    <{request.criterion_uri}> axia:groundsRequirement <{tessera_uri}> .
  }}
}}"""

    await sparql_update(sparql, ds_id)

    await record_provenance_activity(
        ds_id,
        "ValueBasedDesignRequirementCreated",
        user_uri,
        generated=tessera_uri,
        used=[request.criterion_uri],
    )

    logger.info(
        "ValueBasedDesignRequirement aangemaakt: %s in DesignSpace %s door %s",
        tessera_uri, ds_id, user_id,
    )

    return ValueBasedDesignRequirementOut(
        tessera_uri=tessera_uri,
        tessera_id=tessera_id,
        label=request.label,
        criterion_uri=request.criterion_uri,
        created_by=user_id,
        created_at=created_at,
    )


# ---------------------------------------------------------------------------
# US-7.4: GET value-chain
# ---------------------------------------------------------------------------

@router.get("/{ds_id}/value-chain", response_model=ValueChainOut)
async def get_value_chain(
    ds_id: str,
    user: dict = Depends(get_current_user),
) -> ValueChainOut:
    user_id = user["id"]

    has_permission = await check_permission(user_id, ds_id, Role.VIEWER)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Onvoldoende rechten voor deze DesignSpace.")

    graph_uri = f"urn:valor:ds:{ds_id}/baseline"

    query = f"""PREFIX axia: <{AXIA_NS}>
PREFIX cover: <{COVER_NS}>
PREFIX valor: <{VALOR_NS}>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?criterion ?criterionLabel ?valueType ?valueTypeLabel ?requirement ?requirementLabel ?requirementStatus ?capReq WHERE {{
  GRAPH <{graph_uri}> {{
    ?criterion a axia:ValueCriterion ;
               cover:groundedIn ?valueType .
    OPTIONAL {{ ?criterion rdfs:label ?criterionLabel . }}
    OPTIONAL {{ ?valueType rdfs:label ?valueTypeLabel . }}
    OPTIONAL {{
      ?criterion axia:groundsRequirement ?requirement .
      OPTIONAL {{ ?requirement rdfs:label ?requirementLabel . }}
      OPTIONAL {{ ?requirement valor:epistemicStatus ?requirementStatus . }}
      OPTIONAL {{ ?requirement axia:generatesCapabilityRequirement ?capReq . }}
    }}
  }}
}}
ORDER BY ?valueType ?criterion ?requirement"""

    rows = await sparql_select_global(query)

    # Opbouwen geneste structuur: valueType → criteria → requirements
    type_map: dict[str, ValueChainTypeItem] = {}
    criterion_map: dict[str, ValueChainCriterionItem] = {}

    for row in rows:
        value_type_uri = row.get("valueType", "")
        value_type_label = row.get("valueTypeLabel", value_type_uri.rsplit("#", 1)[-1] if "#" in value_type_uri else value_type_uri.rsplit("/", 1)[-1])
        criterion_uri = row.get("criterion", "")
        criterion_label = row.get("criterionLabel", criterion_uri.rsplit(":", 1)[-1])
        criterion_id = criterion_uri.rsplit(":", 1)[-1]
        requirement_uri = row.get("requirement", "")
        requirement_label = row.get("requirementLabel", "")
        req_status_raw = row.get("requirementStatus", "")
        cap_req_uri = row.get("capReq", "")

        if value_type_uri not in type_map:
            type_map[value_type_uri] = ValueChainTypeItem(
                value_type_uri=value_type_uri,
                value_type_label=value_type_label,
                criteria=[],
            )

        if criterion_uri not in criterion_map:
            criterion_item = ValueChainCriterionItem(
                tessera_uri=criterion_uri,
                tessera_id=criterion_id,
                label=criterion_label,
                requirements=[],
            )
            criterion_map[criterion_uri] = criterion_item
            type_map[value_type_uri].criteria.append(criterion_item)

        if requirement_uri:
            req_id = requirement_uri.rsplit(":", 1)[-1]
            req_label = requirement_label or req_id
            req_status_label = req_status_raw.rsplit("#", 1)[-1].rsplit("/", 1)[-1] if (req_status_raw.startswith("http") or req_status_raw.startswith("urn")) else req_status_raw
            req_item = ValueChainRequirementItem(
                tessera_uri=requirement_uri,
                tessera_id=req_id,
                label=req_label,
                epistemic_status=req_status_label or None,
                capability_requirement_uri=cap_req_uri or None,
            )
            # Voorkom duplicaten bij meerdere rows voor dezelfde criterion+requirement
            existing_req_uris = {r.tessera_uri for r in criterion_map[criterion_uri].requirements}
            if requirement_uri not in existing_req_uris:
                criterion_map[criterion_uri].requirements.append(req_item)

    return ValueChainOut(
        design_space_id=ds_id,
        chain=list(type_map.values()),
    )


# ---------------------------------------------------------------------------
# US-7.5: PATCH value-requirement status → CAPAX-propagatie
# ---------------------------------------------------------------------------

class PatchValueRequirementStatusRequest(BaseModel):
    new_status: str


class CapabilityRequirementOut(BaseModel):
    tessera_uri: str
    tessera_id: str
    label: str
    generated_from: str
    epistemic_status: str
    created_by: str
    created_at: str


class PatchValueRequirementStatusResponse(BaseModel):
    tessera_uri: str
    tessera_id: str
    previous_status: str
    new_status: str
    capability_requirement: CapabilityRequirementOut | None = None


@router.patch("/{ds_id}/value-requirement/{req_uri:path}/status", response_model=PatchValueRequirementStatusResponse)
async def patch_value_requirement_status(
    ds_id: str,
    req_uri: str,
    request: PatchValueRequirementStatusRequest,
    user: dict = Depends(get_current_user),
) -> PatchValueRequirementStatusResponse:
    user_id = user["id"]

    has_permission = await check_permission(user_id, ds_id, Role.MEMBER)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Onvoldoende rechten voor deze DesignSpace.")

    graph_uri = f"urn:valor:ds:{ds_id}/baseline"

    # Controleer of het een axia:ValueBasedDesignRequirement is en haal huidige status op
    rows = await sparql_select_global(
        f"""PREFIX axia: <{AXIA_NS}>
PREFIX valor: <{VALOR_NS}>

SELECT ?status ?label WHERE {{
  GRAPH <{graph_uri}> {{
    <{req_uri}> a axia:ValueBasedDesignRequirement ;
               valor:epistemicStatus ?status .
    OPTIONAL {{ <{req_uri}> <http://www.w3.org/2000/01/rdf-schema#label> ?label . }}
  }}
}}"""
    )

    if not rows:
        raise HTTPException(status_code=404, detail="ValueBasedDesignRequirement niet gevonden in deze DesignSpace.")

    current_raw = rows[0]["status"]
    req_label = rows[0].get("label", req_uri.rsplit(":", 1)[-1])

    # Haal de nieuwe status URI op uit de ontologie
    status_label_to_uri = get_status_label_to_uri()
    new_status_uri = status_label_to_uri.get(request.new_status)
    if not new_status_uri:
        raise HTTPException(status_code=422, detail=f"Status '{request.new_status}' niet gevonden in ontologie.")

    if current_raw.startswith("http") or current_raw.startswith("urn"):
        old_status_sparql = f"<{current_raw}>"
        current_status_label = current_raw.rsplit("#", 1)[-1].rsplit("/", 1)[-1]
    else:
        old_status_sparql = f'"{current_raw}"'
        current_status_label = current_raw

    # Update de status van de ValueBasedDesignRequirement
    update = f"""PREFIX valor: <{VALOR_NS}>

DELETE {{
  GRAPH <{graph_uri}> {{
    <{req_uri}> valor:epistemicStatus {old_status_sparql} .
  }}
}}
INSERT {{
  GRAPH <{graph_uri}> {{
    <{req_uri}> valor:epistemicStatus <{new_status_uri}> .
  }}
}}
WHERE {{
  GRAPH <{graph_uri}> {{
    <{req_uri}> valor:epistemicStatus {old_status_sparql} .
  }}
}}"""

    await sparql_update(update, ds_id)

    user_uri = f"urn:valor:user:{user_id}"
    await record_provenance_activity(
        ds_id,
        "ValueRequirementStatusChanged",
        user_uri,
        used=[req_uri],
    )

    logger.info(
        "ValueBasedDesignRequirement %s status: %s → %s (door %s)",
        req_uri, current_status_label, request.new_status, user_id,
    )

    req_tessera_id = req_uri.rsplit(":", 1)[-1]
    capability_out: CapabilityRequirementOut | None = None

    # CAPAX-propagatie: bij Accepted → maak CapabilityRequirement Tessera aan
    if request.new_status == "Accepted":
        cap_req_id = str(uuid.uuid4())
        cap_req_uri = f"urn:valor:tessera:{cap_req_id}"
        created_at = datetime.now(timezone.utc).isoformat()
        proposed_uri = status_label_to_uri.get("Proposed", f"{VALOR_NS}ProposedStatus")
        escaped_label = req_label.replace("\\", "\\\\").replace('"', '\\"')

        cap_sparql = f"""PREFIX axia: <{AXIA_NS}>
PREFIX capax: <{CAPAX_NS}>
PREFIX valor: <{VALOR_NS}>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <{XSD_NS}>

INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{cap_req_uri}> a capax:CapabilityRequirement ;
      a valor:Tessera ;
      rdfs:label "{escaped_label}"@nl ;
      valor:epistemicStatus <{proposed_uri}> ;
      valor:claimedBy <{user_uri}> ;
      valor:claimedAt "{created_at}"^^xsd:dateTime .
    <{req_uri}> axia:generatesCapabilityRequirement <{cap_req_uri}> .
  }}
}}"""

        await sparql_update(cap_sparql, ds_id)

        await record_provenance_activity(
            ds_id,
            "CapabilityRequirementGenerated",
            user_uri,
            generated=cap_req_uri,
            used=[req_uri],
        )

        logger.info(
            "CapabilityRequirement %s aangemaakt via CAPAX-propagatie vanuit %s in DesignSpace %s",
            cap_req_uri, req_uri, ds_id,
        )

        capability_out = CapabilityRequirementOut(
            tessera_uri=cap_req_uri,
            tessera_id=cap_req_id,
            label=req_label,
            generated_from=req_uri,
            epistemic_status="Proposed",
            created_by=user_id,
            created_at=created_at,
        )

    return PatchValueRequirementStatusResponse(
        tessera_uri=req_uri,
        tessera_id=req_tessera_id,
        previous_status=current_status_label,
        new_status=request.new_status,
        capability_requirement=capability_out,
    )


# ---------------------------------------------------------------------------
# US-7.5: GET capability-requirements
# ---------------------------------------------------------------------------

@router.get("/{ds_id}/capability-requirements", response_model=list[CapabilityRequirementOut])
async def get_capability_requirements(
    ds_id: str,
    user: dict = Depends(get_current_user),
) -> list[CapabilityRequirementOut]:
    user_id = user["id"]

    has_permission = await check_permission(user_id, ds_id, Role.VIEWER)
    if not has_permission:
        raise HTTPException(status_code=403, detail="Onvoldoende rechten voor deze DesignSpace.")

    graph_uri = f"urn:valor:ds:{ds_id}:baseline"

    query = f"""PREFIX axia: <{AXIA_NS}>
PREFIX capax: <{CAPAX_NS}>
PREFIX valor: <{VALOR_NS}>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?capReq ?label ?status ?claimedBy ?claimedAt ?generatedFrom WHERE {{
  GRAPH <{graph_uri}> {{
    ?capReq a capax:CapabilityRequirement ;
            valor:epistemicStatus ?status ;
            valor:claimedBy ?claimedBy ;
            valor:claimedAt ?claimedAt .
    OPTIONAL {{ ?capReq rdfs:label ?label . }}
    OPTIONAL {{ ?generatedFrom axia:generatesCapabilityRequirement ?capReq . }}
  }}
}}
ORDER BY ?claimedAt"""

    rows = await sparql_select_global(query)

    result = []
    for row in rows:
        cap_req_uri = row.get("capReq", "")
        cap_req_id = cap_req_uri.rsplit(":", 1)[-1]
        status_raw = row.get("status", "")
        status_label = status_raw.rsplit("#", 1)[-1].rsplit("/", 1)[-1] if (status_raw.startswith("http") or status_raw.startswith("urn")) else status_raw
        claimed_by = row.get("claimedBy", "").rsplit(":", 1)[-1]
        result.append(CapabilityRequirementOut(
            tessera_uri=cap_req_uri,
            tessera_id=cap_req_id,
            label=row.get("label", cap_req_id),
            generated_from=row.get("generatedFrom", ""),
            epistemic_status=status_label,
            created_by=claimed_by,
            created_at=row.get("claimedAt", ""),
        ))

    return result
