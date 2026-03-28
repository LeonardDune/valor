"""Integratietests voor conflictdetectie (US-T.1).

Test:
- ConflictSignal wordt aangemaakt wanneer twee Accepted Tesserae een valor:undermines relatie hebben
- ConflictSignal blijft afwezig wanneer er geen undermines relatie is
- ConflictSignal blijft afwezig wanneer slechts één Tessera Accepted is
- GET /designspace/{ds_id}/conflicts geeft aanwezige ConflictSignals terug
"""
import asyncio
import uuid

import httpx
import pytest

from app.ontology import VALOR_NS
from tests.conftest import FUSEKI_TEST_URL, FUSEKI_TEST_DATASET

pytestmark = pytest.mark.integration

XSD_NS = "http://www.w3.org/2001/XMLSchema#"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _sparql_update(update: str) -> None:
    from tests.conftest import FUSEKI_ADMIN_PASSWORD
    endpoint = f"{FUSEKI_TEST_URL}/{FUSEKI_TEST_DATASET}/update"
    async with httpx.AsyncClient() as client:
        r = await client.post(
            endpoint,
            data={"update": update},
            auth=("admin", FUSEKI_ADMIN_PASSWORD),
            timeout=10,
        )
    r.raise_for_status()


async def _sparql_select(sparql: str) -> list[dict]:
    endpoint = f"{FUSEKI_TEST_URL}/{FUSEKI_TEST_DATASET}/sparql"
    async with httpx.AsyncClient() as client:
        r = await client.post(
            endpoint,
            data={"query": sparql},
            headers={"Accept": "application/sparql-results+json"},
            timeout=10,
        )
    r.raise_for_status()
    return r.json()["results"]["bindings"]


async def _seed_design_space(ds_id: str) -> None:
    from app.services.fuseki import initialize_design_space_graphs
    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")


def _accepted_status_uri() -> str:
    from app.services.ontology_cache import get_status_label_to_uri
    return get_status_label_to_uri()["Accepted"]


def _proposed_status_uri() -> str:
    from app.services.ontology_cache import get_status_label_to_uri
    return get_status_label_to_uri()["Proposed"]


async def _insert_tessera(ds_id: str, tessera_id: str, status_uri: str) -> str:
    """Schrijft een minimale Tessera naar de default graph van ds_id.

    sparql_select(query, ds_id) gebruikt urn:valor:ds:{ds_id} als default-graph-uri,
    dus de data moet in die graph staan zodat _detect_conflicts_async hem vindt.
    """
    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    graph = f"urn:valor:ds:{ds_id}"
    await _sparql_update(f"""PREFIX valor: <{VALOR_NS}>
INSERT DATA {{
  GRAPH <{graph}> {{
    <{tessera_uri}> a valor:Tessera ;
      valor:epistemicStatus <{status_uri}> ;
      valor:claimContent "Testclaim {tessera_id}" .
  }}
}}""")
    return tessera_uri


async def _insert_undermines(ds_id: str, tessera_a_uri: str, tessera_b_uri: str) -> None:
    """Schrijft een valor:undermines triple in de default graph van ds_id."""
    graph = f"urn:valor:ds:{ds_id}"
    await _sparql_update(f"""PREFIX valor: <{VALOR_NS}>
INSERT DATA {{
  GRAPH <{graph}> {{
    <{tessera_a_uri}> valor:undermines <{tessera_b_uri}> .
  }}
}}""")


async def _count_conflict_signals(ds_id: str) -> int:
    prov_graph = f"urn:valor:ds:{ds_id}/provenance"
    rows = await _sparql_select(f"""SELECT (COUNT(?s) AS ?c) WHERE {{
  GRAPH <{prov_graph}> {{
    ?s a <{VALOR_NS}ConflictSignal> .
  }}
}}""")
    return int(rows[0]["c"]["value"]) if rows else 0


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_no_conflict_without_undermines(ds_id: str) -> None:
    """Twee Accepted Tesserae zonder undermines relatie -> geen ConflictSignal."""
    await _seed_design_space(ds_id)
    accepted = _accepted_status_uri()

    tessera_a = await _insert_tessera(ds_id, f"a-{uuid.uuid4().hex[:8]}", accepted)
    tessera_b = await _insert_tessera(ds_id, f"b-{uuid.uuid4().hex[:8]}", accepted)

    from app.routers.tessera import _detect_conflicts_async
    await _detect_conflicts_async(tessera_a, ds_id, accepted)
    await _detect_conflicts_async(tessera_b, ds_id, accepted)

    count = await _count_conflict_signals(ds_id)
    assert count == 0, f"Geen ConflictSignal verwacht, maar {count} gevonden"


async def test_conflict_detected_when_both_accepted(ds_id: str) -> None:
    """Tessera A undermines Tessera B; beide Accepted -> ConflictSignal aangemaakt."""
    await _seed_design_space(ds_id)
    accepted = _accepted_status_uri()

    tessera_a = await _insert_tessera(ds_id, f"a-{uuid.uuid4().hex[:8]}", accepted)
    tessera_b = await _insert_tessera(ds_id, f"b-{uuid.uuid4().hex[:8]}", accepted)
    await _insert_undermines(ds_id, tessera_a, tessera_b)

    from app.routers.tessera import _detect_conflicts_async

    # Simuleer: eerst A Accepted (B nog niet Accepted, dus geen conflict).
    # Dan B Accepted (A is al Accepted, dus conflict).
    await _detect_conflicts_async(tessera_b, ds_id, accepted)

    count = await _count_conflict_signals(ds_id)
    assert count == 1, f"Precies 1 ConflictSignal verwacht, maar {count} gevonden"

    # Verifieer inhoud van het ConflictSignal
    prov_graph = f"urn:valor:ds:{ds_id}/provenance"
    rows = await _sparql_select(f"""SELECT ?signal ?ta ?tb ?det WHERE {{
  GRAPH <{prov_graph}> {{
    ?signal a <{VALOR_NS}ConflictSignal> ;
      <{VALOR_NS}conflictingTessera> ?ta ;
      <{VALOR_NS}conflictingTessera> ?tb ;
      <{VALOR_NS}detectedAt> ?det .
    FILTER(?ta != ?tb)
  }}
}}""")
    assert rows, "ConflictSignal triples niet volledig aanwezig in provenance graph"
    tessera_uris = {rows[0]["ta"]["value"], rows[0]["tb"]["value"]}
    assert tessera_a in tessera_uris, f"{tessera_a} niet in conflictingTessera triples"
    assert tessera_b in tessera_uris, f"{tessera_b} niet in conflictingTessera triples"
    assert rows[0]["det"]["value"], "valor:detectedAt is leeg"


async def test_no_conflict_when_only_one_accepted(ds_id: str) -> None:
    """Tessera A undermines Tessera B; alleen A is Accepted -> geen ConflictSignal."""
    await _seed_design_space(ds_id)
    accepted = _accepted_status_uri()
    proposed = _proposed_status_uri()

    tessera_a = await _insert_tessera(ds_id, f"a-{uuid.uuid4().hex[:8]}", accepted)
    tessera_b = await _insert_tessera(ds_id, f"b-{uuid.uuid4().hex[:8]}", proposed)
    await _insert_undermines(ds_id, tessera_a, tessera_b)

    from app.routers.tessera import _detect_conflicts_async
    await _detect_conflicts_async(tessera_a, ds_id, accepted)

    count = await _count_conflict_signals(ds_id)
    assert count == 0, f"Geen ConflictSignal verwacht (B is Proposed), maar {count} gevonden"


async def test_get_conflicts_endpoint_returns_signals(ds_id: str) -> None:
    """GET /designspace/{ds_id}/conflicts geeft ConflictSignal data terug.

    Schrijft een ConflictSignal direct naar de provenance graph en verifieert
    dat het endpoint dit correct teruggeeft.
    """

    tessera_a_uri = f"urn:valor:tessera:conflict-a-{uuid.uuid4().hex[:8]}"
    tessera_b_uri = f"urn:valor:tessera:conflict-b-{uuid.uuid4().hex[:8]}"
    conflict_uri = f"urn:valor:conflict:{uuid.uuid4()}"
    prov_graph = f"urn:valor:ds:{ds_id}/provenance"
    detected_at = "2026-01-01T12:00:00+00:00"

    await _sparql_update(f"""PREFIX valor: <{VALOR_NS}>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
INSERT DATA {{
  GRAPH <{prov_graph}> {{
    <{conflict_uri}> a valor:ConflictSignal ;
      valor:conflictingTessera <{tessera_a_uri}> ;
      valor:conflictingTessera <{tessera_b_uri}> ;
      valor:detectedAt "{detected_at}"^^xsd:dateTime .
  }}
}}""")

    import app.routers.designspace as ds_router
    original_check = ds_router.check_permission

    async def _allow_all(*args, **kwargs):
        return True

    ds_router.check_permission = _allow_all
    try:
        from app.routers.designspace import get_conflicts
        result = await get_conflicts(
            design_space_id=ds_id,
            user={"id": "test-user-001"},
        )
    finally:
        ds_router.check_permission = original_check

    assert isinstance(result, list), "Verwacht een lijst"
    assert len(result) == 1, f"Verwacht 1 conflict, maar {len(result)} gevonden"

    conflict = result[0]
    assert conflict["conflict_uri"] == conflict_uri
    tessera_uris = {conflict["tessera_a"], conflict["tessera_b"]}
    assert tessera_a_uri in tessera_uris
    assert tessera_b_uri in tessera_uris
    assert conflict["detected_at"] == detected_at
