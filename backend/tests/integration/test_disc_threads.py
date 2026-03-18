"""Integratietests voor disc:DiscussionThread aanmaken en ophalen (US-16.2).

Verifieert:
- create_discussion_thread schrijft correcte triples naar Fuseki
- get_threads_by_tessera retourneert de juiste threads
- Meerdere threads per tessera worden correct teruggegeven
"""
import pytest

from app.db.disc import create_discussion_thread, get_threads_by_tessera
from app.services.fuseki import named_graph_uri

pytestmark = pytest.mark.integration

DISC_NS = "https://valor-ecosystem.nl/ontology/disc#"
PROV_NS = "https://www.w3.org/ns/prov#"

TESSERA_A = "tessera-disc-test-001"
TESSERA_B = "tessera-disc-test-002"
USER_ID = "user-disc-test-001"


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


# ---------------------------------------------------------------------------
# create_discussion_thread
# ---------------------------------------------------------------------------

async def test_create_thread_retourneert_thread_id(ds_id):
    thread_id = await create_discussion_thread(TESSERA_A, ds_id, USER_ID)
    assert thread_id, "thread_id mag niet leeg zijn"
    assert len(thread_id) == 36, "thread_id moet een UUID zijn"


async def test_create_thread_schrijft_type_triple(ds_id):
    thread_id = await create_discussion_thread(TESSERA_A, ds_id, USER_ID)
    thread_uri = f"urn:valor:thread:{thread_id}"
    graph = named_graph_uri(ds_id)

    rows = await _sparql_select(graph, f"""
        PREFIX disc: <{DISC_NS}>
        SELECT ?thread WHERE {{
          GRAPH <{graph}> {{
            <{thread_uri}> a disc:DiscussionThread .
            BIND(<{thread_uri}> AS ?thread)
          }}
        }}
    """)
    assert rows, "disc:DiscussionThread-triple ontbreekt in Fuseki"


async def test_create_thread_schrijft_about_tessera(ds_id):
    thread_id = await create_discussion_thread(TESSERA_A, ds_id, USER_ID)
    thread_uri = f"urn:valor:thread:{thread_id}"
    tessera_uri = f"urn:valor:tessera:{TESSERA_A}"
    graph = named_graph_uri(ds_id)

    rows = await _sparql_select(graph, f"""
        PREFIX disc: <{DISC_NS}>
        SELECT ?tessera WHERE {{
          GRAPH <{graph}> {{
            <{thread_uri}> disc:aboutTessera ?tessera .
          }}
        }}
    """)
    assert rows, "disc:aboutTessera-triple ontbreekt"
    assert rows[0]["tessera"]["value"] == tessera_uri


async def test_create_thread_schrijft_prov_triples(ds_id):
    thread_id = await create_discussion_thread(TESSERA_A, ds_id, USER_ID)
    thread_uri = f"urn:valor:thread:{thread_id}"
    user_uri = f"urn:valor:user:{USER_ID}"
    graph = named_graph_uri(ds_id)

    rows = await _sparql_select(graph, f"""
        PREFIX prov: <{PROV_NS}>
        SELECT ?started_by ?started_at WHERE {{
          GRAPH <{graph}> {{
            <{thread_uri}> prov:wasStartedBy ?started_by ;
                           prov:startedAtTime ?started_at .
          }}
        }}
    """)
    assert rows, "prov:wasStartedBy / prov:startedAtTime ontbreken"
    assert rows[0]["started_by"]["value"] == user_uri
    assert rows[0]["started_at"]["value"], "startedAtTime mag niet leeg zijn"


# ---------------------------------------------------------------------------
# get_threads_by_tessera
# ---------------------------------------------------------------------------

async def test_get_threads_retourneert_lege_lijst_zonder_data(ds_id):
    result = await get_threads_by_tessera(TESSERA_A, ds_id)
    assert result == []


async def test_get_threads_retourneert_aangemaakte_thread(ds_id):
    thread_id = await create_discussion_thread(TESSERA_A, ds_id, USER_ID)
    result = await get_threads_by_tessera(TESSERA_A, ds_id)

    assert len(result) == 1
    assert result[0]["thread_id"] == thread_id
    assert result[0]["tessera_id"] == TESSERA_A
    assert result[0]["design_space_id"] == ds_id
    assert result[0]["started_by"] == f"urn:valor:user:{USER_ID}"


async def test_get_threads_retourneert_meerdere_threads(ds_id):
    tid1 = await create_discussion_thread(TESSERA_A, ds_id, USER_ID)
    tid2 = await create_discussion_thread(TESSERA_A, ds_id, USER_ID)

    result = await get_threads_by_tessera(TESSERA_A, ds_id)
    assert len(result) == 2
    thread_ids = {r["thread_id"] for r in result}
    assert tid1 in thread_ids
    assert tid2 in thread_ids


async def test_get_threads_isoleert_per_tessera(ds_id):
    """Threads van tessera A mogen niet in resultaat van tessera B verschijnen."""
    await create_discussion_thread(TESSERA_A, ds_id, USER_ID)

    result_b = await get_threads_by_tessera(TESSERA_B, ds_id)
    assert result_b == [], "Thread van tessera A mag niet verschijnen bij tessera B"
