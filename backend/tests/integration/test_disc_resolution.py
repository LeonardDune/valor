"""Integratietests voor disc:ThreadResolution (US-16.4).

Verifieert:
- create_thread_resolution schrijft correcte triples naar Fuseki
- disc:hasResolution koppelt resolution aan thread
- disc:motivatesArgue koppelt resolution aan tessera
- disc:resolutionOutcome bevat de juiste status-URI
- get_thread_tessera retourneert de juiste tessera_uri
"""
import pytest

from app.db.disc import (
    create_discussion_thread,
    create_thread_resolution,
    get_thread_tessera,
)
from app.services.fuseki import named_graph_uri, sparql_update

pytestmark = pytest.mark.integration

DISC_NS = "https://valor-ecosystem.nl/ontology/disc#"
PROV_NS = "https://www.w3.org/ns/prov#"
VALOR_NS = "https://valor-ecosystem.nl/ontology/"

TESSERA_ID = "tessera-resolution-test-001"
USER_ID = "user-resolution-test-001"
OUTCOME_URI = f"{VALOR_NS}ContestedStatus"


async def _sparql_select(graph_uri: str, query: str) -> list[dict]:
    import httpx
    from tests.conftest import FUSEKI_TEST_URL, FUSEKI_TEST_DATASET

    endpoint = f"{FUSEKI_TEST_URL}/{FUSEKI_TEST_DATASET}/sparql"
    async with httpx.AsyncClient() as client:
        r = await client.post(
            endpoint,
            data={"query": query},
            headers={"Accept": "application/sparql-results+json"},
            timeout=10,
        )
    r.raise_for_status()
    return r.json()["results"]["bindings"]


@pytest.fixture
async def tessera_seeded(ds_id) -> str:
    """Seed een Tessera in Fuseki voor gebruik in resolution-tests."""
    tessera_uri = f"urn:valor:tessera:{TESSERA_ID}"
    graph = named_graph_uri(ds_id)
    proposed_uri = f"{VALOR_NS}ProposedStatus"

    await sparql_update(f"""PREFIX valor: <{VALOR_NS}>
INSERT DATA {{
  GRAPH <{graph}> {{
    <{tessera_uri}> a valor:Tessera ;
      valor:epistemicStatus <{proposed_uri}> ;
      valor:claimContent "Testclaim"@nl .
  }}
}}""", ds_id)
    return TESSERA_ID


@pytest.fixture
async def thread_id(ds_id, tessera_seeded) -> str:
    return await create_discussion_thread(tessera_seeded, ds_id, USER_ID)


# ---------------------------------------------------------------------------
# get_thread_tessera
# ---------------------------------------------------------------------------

async def test_get_thread_tessera_retourneert_tessera_uri(ds_id, thread_id):
    result = await get_thread_tessera(thread_id, ds_id)
    assert result == f"urn:valor:tessera:{TESSERA_ID}"


async def test_get_thread_tessera_retourneert_none_voor_onbekende_thread(ds_id):
    result = await get_thread_tessera("onbekende-thread-id", ds_id)
    assert result is None


# ---------------------------------------------------------------------------
# create_thread_resolution
# ---------------------------------------------------------------------------

async def test_create_resolution_retourneert_resolution_id(ds_id, thread_id):
    tessera_uri = f"urn:valor:tessera:{TESSERA_ID}"
    resolution_id = await create_thread_resolution(
        thread_id=thread_id,
        design_space_id=ds_id,
        user_id=USER_ID,
        resolution_outcome_uri=OUTCOME_URI,
        resolution_rationale="Klopt niet op basis van de discussie.",
        tessera_uri=tessera_uri,
    )
    assert resolution_id, "resolution_id mag niet leeg zijn"
    assert len(resolution_id) == 36, "resolution_id moet een UUID zijn"


async def test_create_resolution_schrijft_type_triple(ds_id, thread_id):
    tessera_uri = f"urn:valor:tessera:{TESSERA_ID}"
    resolution_id = await create_thread_resolution(
        thread_id=thread_id,
        design_space_id=ds_id,
        user_id=USER_ID,
        resolution_outcome_uri=OUTCOME_URI,
        resolution_rationale="Testrationale.",
        tessera_uri=tessera_uri,
    )
    resolution_uri = f"urn:valor:resolution:{resolution_id}"
    graph = named_graph_uri(ds_id)

    rows = await _sparql_select(graph, f"""
        PREFIX disc: <{DISC_NS}>
        SELECT ?r WHERE {{
          GRAPH <{graph}> {{
            <{resolution_uri}> a disc:ThreadResolution .
            BIND(<{resolution_uri}> AS ?r)
          }}
        }}
    """)
    assert rows, "disc:ThreadResolution-triple ontbreekt"


async def test_create_resolution_schrijft_outcome(ds_id, thread_id):
    tessera_uri = f"urn:valor:tessera:{TESSERA_ID}"
    resolution_id = await create_thread_resolution(
        thread_id=thread_id,
        design_space_id=ds_id,
        user_id=USER_ID,
        resolution_outcome_uri=OUTCOME_URI,
        resolution_rationale="Testrationale.",
        tessera_uri=tessera_uri,
    )
    resolution_uri = f"urn:valor:resolution:{resolution_id}"
    graph = named_graph_uri(ds_id)

    rows = await _sparql_select(graph, f"""
        PREFIX disc: <{DISC_NS}>
        SELECT ?outcome WHERE {{
          GRAPH <{graph}> {{
            <{resolution_uri}> disc:resolutionOutcome ?outcome .
          }}
        }}
    """)
    assert rows, "disc:resolutionOutcome ontbreekt"
    assert rows[0]["outcome"]["value"] == OUTCOME_URI


async def test_create_resolution_koppelt_aan_thread(ds_id, thread_id):
    tessera_uri = f"urn:valor:tessera:{TESSERA_ID}"
    resolution_id = await create_thread_resolution(
        thread_id=thread_id,
        design_space_id=ds_id,
        user_id=USER_ID,
        resolution_outcome_uri=OUTCOME_URI,
        resolution_rationale="Testrationale.",
        tessera_uri=tessera_uri,
    )
    resolution_uri = f"urn:valor:resolution:{resolution_id}"
    thread_uri = f"urn:valor:thread:{thread_id}"
    graph = named_graph_uri(ds_id)

    rows = await _sparql_select(graph, f"""
        PREFIX disc: <{DISC_NS}>
        SELECT ?r WHERE {{
          GRAPH <{graph}> {{
            <{thread_uri}> disc:hasResolution <{resolution_uri}> .
            BIND(<{resolution_uri}> AS ?r)
          }}
        }}
    """)
    assert rows, "disc:hasResolution-koppeling ontbreekt"


async def test_create_resolution_schrijft_motivates_argue(ds_id, thread_id):
    tessera_uri = f"urn:valor:tessera:{TESSERA_ID}"
    resolution_id = await create_thread_resolution(
        thread_id=thread_id,
        design_space_id=ds_id,
        user_id=USER_ID,
        resolution_outcome_uri=OUTCOME_URI,
        resolution_rationale="Testrationale.",
        tessera_uri=tessera_uri,
    )
    resolution_uri = f"urn:valor:resolution:{resolution_id}"
    graph = named_graph_uri(ds_id)

    rows = await _sparql_select(graph, f"""
        PREFIX disc: <{DISC_NS}>
        SELECT ?target WHERE {{
          GRAPH <{graph}> {{
            <{resolution_uri}> disc:motivatesArgue ?target .
          }}
        }}
    """)
    assert rows, "disc:motivatesArgue-triple ontbreekt"
    assert rows[0]["target"]["value"] == tessera_uri


async def test_create_resolution_schrijft_prov_triples(ds_id, thread_id):
    tessera_uri = f"urn:valor:tessera:{TESSERA_ID}"
    resolution_id = await create_thread_resolution(
        thread_id=thread_id,
        design_space_id=ds_id,
        user_id=USER_ID,
        resolution_outcome_uri=OUTCOME_URI,
        resolution_rationale="Testrationale.",
        tessera_uri=tessera_uri,
    )
    resolution_uri = f"urn:valor:resolution:{resolution_id}"
    user_uri = f"urn:valor:user:{USER_ID}"
    graph = named_graph_uri(ds_id)

    rows = await _sparql_select(graph, f"""
        PREFIX prov: <{PROV_NS}>
        SELECT ?attr ?gen WHERE {{
          GRAPH <{graph}> {{
            <{resolution_uri}> prov:wasAttributedTo ?attr ;
                               prov:generatedAtTime ?gen .
          }}
        }}
    """)
    assert rows, "prov:wasAttributedTo / prov:generatedAtTime ontbreken"
    assert rows[0]["attr"]["value"] == user_uri
    assert rows[0]["gen"]["value"], "generatedAtTime mag niet leeg zijn"
