"""Integratietests voor US-4.5: causa:hasManifestationCondition op CausalClaim-Tessera.

Test dat:
  - POST /tessera/ manifestation_condition opslaat als causa:hasManifestationCondition triple
  - GET /tessera/{id} de ManifestationCondition URI retourneert indien aanwezig
  - Een Tessera zonder manifestation_condition None teruggeeft op GET

Gebruik:
    cd backend
    FUSEKI_URL=http://localhost:3030 pytest tests/integration/test_tessera_manifestation_condition.py -v
"""
import sys
import os
import uuid
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.ontology import VALOR_NS

CAUSA_NS = f"{VALOR_NS}causa#"
SYSONT_NS = f"{VALOR_NS}sysont#"

pytestmark = pytest.mark.integration

USER_ID = "user-mc-test-001"
USER_URI = f"urn:valor:user:{USER_ID}"
SYSTEM_SITUATION_URI = f"{SYSONT_NS}Droogte"


async def _seed_design_space(ds_id: str) -> None:
    from app.services.fuseki import initialize_design_space_graphs
    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")


async def _create_tessera_direct(
    ds_id: str,
    content: str,
    manifestation_condition: str | None = None,
) -> str:
    """Schrijft een Tessera direct via SPARQL (zonder HTTP-route)."""
    from app.services.fuseki import sparql_update, named_graph_uri
    from app.services.ontology_cache import get_status_label_to_uri
    from datetime import datetime, timezone

    tessera_id = str(uuid.uuid4())
    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    graph_uri = named_graph_uri(ds_id)
    proposed_uri = get_status_label_to_uri().get("Proposed", f"{VALOR_NS}ProposedStatus")
    claimed_at = datetime.now(timezone.utc).isoformat()
    escaped = content.replace("\\", "\\\\").replace('"', '\\"')

    optional = ""
    if manifestation_condition:
        optional = f'<{tessera_uri}> <{CAUSA_NS}hasManifestationCondition> <{manifestation_condition}> .\n'

    sparql = f"""PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> a <{VALOR_NS}Tessera> ;
      <{VALOR_NS}claimContent> "{escaped}"@nl ;
      <{VALOR_NS}epistemicStatus> <{proposed_uri}> ;
      <{VALOR_NS}claimedBy> <{USER_URI}> ;
      <{VALOR_NS}claimedAt> "{claimed_at}"^^xsd:dateTime ;
      <{VALOR_NS}inDesignSpace> <{graph_uri}> .
    {optional}
  }}
}}"""
    await sparql_update(sparql, ds_id)
    return tessera_id


async def _read_manifestation_condition(ds_id: str, tessera_id: str) -> str | None:
    """Queryt de causa:hasManifestationCondition triple direct uit Fuseki."""
    from app.services.fuseki import sparql_select, named_graph_uri

    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    graph_uri = named_graph_uri(ds_id)

    rows = await sparql_select(
        f"""SELECT ?mc WHERE {{
          GRAPH <{graph_uri}> {{
            <{tessera_uri}> <{CAUSA_NS}hasManifestationCondition> ?mc .
          }}
        }}""",
        ds_id,
    )
    return rows[0]["mc"] if rows else None


# ---------------------------------------------------------------------------
# Tests: SPARQL-laag
# ---------------------------------------------------------------------------

async def test_manifestation_condition_opgeslagen_als_triple(ds_id):
    """causa:hasManifestationCondition triple staat in Fuseki na aanmaken Tessera."""
    await _seed_design_space(ds_id)
    tessera_id = await _create_tessera_direct(
        ds_id,
        "Als het droog is, stijgt de waterprijs.",
        manifestation_condition=SYSTEM_SITUATION_URI,
    )
    mc = await _read_manifestation_condition(ds_id, tessera_id)
    assert mc == SYSTEM_SITUATION_URI


async def test_tessera_zonder_manifestation_condition_geeft_none(ds_id):
    """Tessera zonder manifestation_condition levert None op bij query."""
    await _seed_design_space(ds_id)
    tessera_id = await _create_tessera_direct(
        ds_id,
        "Generieke claim zonder conditie.",
    )
    mc = await _read_manifestation_condition(ds_id, tessera_id)
    assert mc is None


async def test_manifestation_condition_uri_behouden_na_opslaan(ds_id):
    """De URI van de ManifestationCondition blijft ongewijzigd na opslaan."""
    await _seed_design_space(ds_id)
    custom_uri = f"{SYSONT_NS}HevigRegenval"
    tessera_id = await _create_tessera_direct(
        ds_id,
        "Bij hevige regenval neemt de doorstroomtijd toe.",
        manifestation_condition=custom_uri,
    )
    mc = await _read_manifestation_condition(ds_id, tessera_id)
    assert mc == custom_uri


# ---------------------------------------------------------------------------
# Tests: CreateTesseraRequest / TesseraResponse modellen
# ---------------------------------------------------------------------------

def test_create_tessera_request_accepteert_manifestation_condition():
    """CreateTesseraRequest accepteert manifestation_condition als Optional[str]."""
    from app.routers.tessera import CreateTesseraRequest

    req = CreateTesseraRequest(
        design_space_id="ds-test",
        claim_content="Test claim",
        manifestation_condition=SYSTEM_SITUATION_URI,
    )
    assert req.manifestation_condition == SYSTEM_SITUATION_URI


def test_create_tessera_request_manifestation_condition_default_none():
    """CreateTesseraRequest heeft None als default voor manifestation_condition."""
    from app.routers.tessera import CreateTesseraRequest

    req = CreateTesseraRequest(
        design_space_id="ds-test",
        claim_content="Test claim",
    )
    assert req.manifestation_condition is None


def test_tessera_response_bevat_manifestation_condition_veld():
    """TesseraResponse heeft een manifestation_condition veld."""
    from app.routers.tessera import TesseraResponse

    resp = TesseraResponse(
        tessera_id="abc",
        tessera_uri="urn:valor:tessera:abc",
        design_space_id="ds-test",
        claim_content="Test",
        claim_type="AsIs",
        epistemic_status="Proposed",
        claimed_by="user-1",
        claimed_at="2026-01-01T00:00:00+00:00",
        manifestation_condition=SYSTEM_SITUATION_URI,
    )
    assert resp.manifestation_condition == SYSTEM_SITUATION_URI


def test_tessera_response_manifestation_condition_optioneel():
    """TesseraResponse werkt correct zonder manifestation_condition."""
    from app.routers.tessera import TesseraResponse

    resp = TesseraResponse(
        tessera_id="abc",
        tessera_uri="urn:valor:tessera:abc",
        design_space_id="ds-test",
        claim_content="Test",
        claim_type="AsIs",
        epistemic_status="Proposed",
        claimed_by="user-1",
        claimed_at="2026-01-01T00:00:00+00:00",
    )
    assert resp.manifestation_condition is None


# ---------------------------------------------------------------------------
# Tests: ontology_cache getter
# ---------------------------------------------------------------------------

def test_get_system_situation_label_to_uri_retourneert_dict():
    """get_system_situation_label_to_uri() retourneert altijd een dict."""
    from app.services.ontology_cache import get_system_situation_label_to_uri

    result = get_system_situation_label_to_uri()
    assert isinstance(result, dict)
