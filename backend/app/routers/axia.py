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
