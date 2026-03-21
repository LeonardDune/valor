"""Integratietests voor PROV-O provenance logging (app.services.fuseki).

Test:
- record_provenance_activity schrijft een prov:Activity naar de provenance-graph
- Verplichte velden aanwezig: prov:wasAttributedTo, prov:startedAtTime, operationType
- prov:generated en prov:used worden correct geschreven
- activity_uri is uniek per aanroep
"""
import pytest

pytestmark = pytest.mark.integration

PROV_NS = "https://www.w3.org/ns/prov#"


async def _query_prov_graph(ds_id: str, sparql: str) -> list[dict]:
    import httpx
    from tests.conftest import FUSEKI_TEST_URL, FUSEKI_TEST_DATASET

    endpoint = f"{FUSEKI_TEST_URL}/{FUSEKI_TEST_DATASET}/sparql"
    prov_graph = f"urn:valor:ds:{ds_id}/provenance"
    async with httpx.AsyncClient() as client:
        r = await client.post(
            endpoint,
            data={"query": sparql.replace("__PROV_GRAPH__", prov_graph)},
            headers={"Accept": "application/sparql-results+json"},
            timeout=10,
        )
    r.raise_for_status()
    return r.json()["results"]["bindings"]


# ---------------------------------------------------------------------------
# Basisstructuur
# ---------------------------------------------------------------------------

async def test_record_provenance_activity_schrijft_activity(ds_id, user_uri):
    from app.services.fuseki import (
        initialize_design_space_graphs,
        record_provenance_activity,
    )

    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")
    activity_uri = await record_provenance_activity(
        ds_id=ds_id,
        operation_type="TesseraCreated",
        user_uri=user_uri,
    )

    assert activity_uri.startswith("urn:valor:activity:")

    rows = await _query_prov_graph(ds_id, f"""
        SELECT ?p ?o WHERE {{
          GRAPH <__PROV_GRAPH__> {{
            <{activity_uri}> ?p ?o .
          }}
        }}
    """)
    assert rows, "Geen triples gevonden voor de activity"


async def test_record_provenance_activity_bevat_type_activity(ds_id, user_uri):
    from app.services.fuseki import initialize_design_space_graphs, record_provenance_activity

    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")
    activity_uri = await record_provenance_activity(ds_id, "TesseraCreated", user_uri)

    rows = await _query_prov_graph(ds_id, f"""
        SELECT ?type WHERE {{
          GRAPH <__PROV_GRAPH__> {{
            <{activity_uri}> a ?type .
          }}
        }}
    """)
    types = {row["type"]["value"] for row in rows}
    assert f"{PROV_NS}Activity" in types


async def test_record_provenance_activity_bevat_attributed_to(ds_id, user_uri):
    from app.services.fuseki import initialize_design_space_graphs, record_provenance_activity

    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")
    activity_uri = await record_provenance_activity(ds_id, "TesseraCreated", user_uri)

    rows = await _query_prov_graph(ds_id, f"""
        SELECT ?agent WHERE {{
          GRAPH <__PROV_GRAPH__> {{
            <{activity_uri}> <{PROV_NS}wasAttributedTo> ?agent .
          }}
        }}
    """)
    assert rows
    assert rows[0]["agent"]["value"] == user_uri


async def test_record_provenance_activity_bevat_started_at_time(ds_id, user_uri):
    from app.services.fuseki import initialize_design_space_graphs, record_provenance_activity

    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")
    activity_uri = await record_provenance_activity(ds_id, "StatusChanged", user_uri)

    rows = await _query_prov_graph(ds_id, f"""
        SELECT ?t WHERE {{
          GRAPH <__PROV_GRAPH__> {{
            <{activity_uri}> <{PROV_NS}startedAtTime> ?t .
          }}
        }}
    """)
    assert rows, "Geen startedAtTime gevonden"


async def test_record_provenance_activity_bevat_operation_type(ds_id, user_uri):
    from app.services.fuseki import initialize_design_space_graphs, record_provenance_activity

    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")
    activity_uri = await record_provenance_activity(ds_id, "ArgumentAdded", user_uri)

    rows = await _query_prov_graph(ds_id, f"""
        SELECT ?op WHERE {{
          GRAPH <__PROV_GRAPH__> {{
            <{activity_uri}> <urn:valor:operationType> ?op .
          }}
        }}
    """)
    assert rows
    assert "ArgumentAdded" in rows[0]["op"]["value"]


# ---------------------------------------------------------------------------
# prov:generated en prov:used
# ---------------------------------------------------------------------------

async def test_record_provenance_activity_schrijft_generated(ds_id, user_uri):
    from app.services.fuseki import initialize_design_space_graphs, record_provenance_activity

    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")
    tessera_uri = f"urn:valor:tessera:gen-factor-test"
    activity_uri = await record_provenance_activity(
        ds_id, "TesseraCreated", user_uri,
        generated=tessera_uri,
    )

    rows = await _query_prov_graph(ds_id, f"""
        SELECT ?gen WHERE {{
          GRAPH <__PROV_GRAPH__> {{
            <{activity_uri}> <{PROV_NS}generated> ?gen .
          }}
        }}
    """)
    assert rows
    assert rows[0]["gen"]["value"] == tessera_uri


async def test_record_provenance_activity_schrijft_used_lijst(ds_id, user_uri):
    from app.services.fuseki import initialize_design_space_graphs, record_provenance_activity

    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")
    used = ["urn:valor:tessera:src", "urn:valor:tessera:tgt"]
    activity_uri = await record_provenance_activity(
        ds_id, "ArgumentAdded", user_uri,
        used=used,
    )

    rows = await _query_prov_graph(ds_id, f"""
        SELECT ?res WHERE {{
          GRAPH <__PROV_GRAPH__> {{
            <{activity_uri}> <{PROV_NS}used> ?res .
          }}
        }}
    """)
    found = {row["res"]["value"] for row in rows}
    assert used[0] in found
    assert used[1] in found


# ---------------------------------------------------------------------------
# Uniciteit van activity URI's
# ---------------------------------------------------------------------------

async def test_record_provenance_activity_genereert_unieke_uri_per_aanroep(ds_id, user_uri):
    from app.services.fuseki import initialize_design_space_graphs, record_provenance_activity

    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")
    uri_1 = await record_provenance_activity(ds_id, "TesseraCreated", user_uri)
    uri_2 = await record_provenance_activity(ds_id, "TesseraCreated", user_uri)

    assert uri_1 != uri_2, "Elke activity moet een unieke URI krijgen"
