import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_user
from app.db.permissions import check_permission
from app.models.domain import Role
from app.services.fuseki import sparql_select, sparql_update, record_provenance_activity
from app.ontology import VALOR_NS

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/designspace",
    tags=["axia"],
)

AXIA_NS = "https://valor-ecosystem.nl/ontology/axia#"
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
    claimed_by: str
    claimed_at: str


class ValueCanvasOut(BaseModel):
    design_space_id: str
    groups: dict[str, list[ValueClaimOut]]


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

    graph_uri = f"urn:valor:ds:{ds_id}:baseline"

    query = f"""PREFIX axia: <{AXIA_NS}>
PREFIX cover: <{COVER_NS}>
PREFIX valor: <{VALOR_NS}>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?tessera ?content ?valueType ?valueTypeLabel ?claimedBy ?claimedAt WHERE {{
  GRAPH <{graph_uri}> {{
    ?tessera a axia:ValueClaim ;
             valor:claimContent ?content ;
             valor:claimedBy ?claimedBy ;
             valor:claimedAt ?claimedAt .
    OPTIONAL {{
      ?tessera axia:groundedIn ?valueType .
    }}
    OPTIONAL {{
      ?tessera axia:valueType ?valueType .
    }}
    OPTIONAL {{
      ?valueType rdfs:label ?valueTypeLabel .
    }}
  }}
}}
ORDER BY ?valueType"""

    rows = await sparql_select(query, ds_id)

    groups: dict[str, list[ValueClaimOut]] = {}
    for row in rows:
        tessera_uri = row.get("tessera", "")
        tessera_id = tessera_uri.rsplit(":", 1)[-1]
        value_type_uri = row.get("valueType", "")
        value_type_label = row.get("valueTypeLabel", value_type_uri.rsplit("#", 1)[-1] if "#" in value_type_uri else value_type_uri.rsplit("/", 1)[-1])

        claim = ValueClaimOut(
            tessera_uri=tessera_uri,
            tessera_id=tessera_id,
            claim_content=row.get("content", ""),
            value_type_uri=value_type_uri,
            value_type_label=value_type_label,
            claimed_by=row.get("claimedBy", "").rsplit(":", 1)[-1],
            claimed_at=row.get("claimedAt", ""),
        )

        groups.setdefault(value_type_uri, []).append(claim)

    return ValueCanvasOut(design_space_id=ds_id, groups=groups)


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
    graph_uri = f"urn:valor:ds:{ds_id}:baseline"

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

    graph_uri = f"urn:valor:ds:{ds_id}:baseline"

    query = f"""PREFIX axia: <{AXIA_NS}>

SELECT ?factor (COUNT(?implication) AS ?count) WHERE {{
  GRAPH <{graph_uri}> {{
    ?implication a axia:DesignImplication ;
                 axia:impliesFor ?factor .
  }}
}}
GROUP BY ?factor
ORDER BY DESC(?count)"""

    rows = await sparql_select(query, ds_id)

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
    graph_uri = f"urn:valor:ds:{ds_id}:baseline"

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
    graph_uri = f"urn:valor:ds:{ds_id}:baseline"

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

    graph_uri = f"urn:valor:ds:{ds_id}:baseline"

    query = f"""PREFIX axia: <{AXIA_NS}>
PREFIX cover: <{COVER_NS}>
PREFIX valor: <{VALOR_NS}>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?criterion ?criterionLabel ?valueType ?valueTypeLabel ?requirement ?requirementLabel WHERE {{
  GRAPH <{graph_uri}> {{
    ?criterion a axia:ValueCriterion ;
               cover:groundedIn ?valueType .
    OPTIONAL {{ ?criterion rdfs:label ?criterionLabel . }}
    OPTIONAL {{ ?valueType rdfs:label ?valueTypeLabel . }}
    OPTIONAL {{
      ?criterion axia:groundsRequirement ?requirement .
      OPTIONAL {{ ?requirement rdfs:label ?requirementLabel . }}
    }}
  }}
}}
ORDER BY ?valueType ?criterion ?requirement"""

    rows = await sparql_select(query, ds_id)

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
            req_item = ValueChainRequirementItem(
                tessera_uri=requirement_uri,
                tessera_id=req_id,
                label=req_label,
            )
            # Voorkom duplicaten bij meerdere rows voor dezelfde criterion+requirement
            existing_req_uris = {r.tessera_uri for r in criterion_map[criterion_uri].requirements}
            if requirement_uri not in existing_req_uris:
                criterion_map[criterion_uri].requirements.append(req_item)

    return ValueChainOut(
        design_space_id=ds_id,
        chain=list(type_map.values()),
    )
