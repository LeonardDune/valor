"""Integratietests voor disc:ThreadContribution aanmaken en ophalen (US-16.3).

Verifieert:
- create_thread_contribution schrijft correcte triples naar Fuseki
- PROV-O: prov:wasAssociatedWith + prov:endedAtTime aanwezig
- disc:hasContribution koppelt bijdrage aan thread
- disc:attachesEvidence correct opgeslagen indien evidence meegegeven
- get_contributions_by_thread retourneert bijdragen gesorteerd op tijd
"""
import pytest

from app.db.disc import create_discussion_thread, create_thread_contribution, get_contributions_by_thread
from app.services.fuseki import named_graph_uri

pytestmark = pytest.mark.integration

DISC_NS = "https://valor-ecosystem.nl/ontology/disc#"
PROV_NS = "https://www.w3.org/ns/prov#"
VALOR_BASE = "https://valor-ecosystem.nl/ontology/"

TESSERA_ID = "tessera-contrib-test-001"
USER_ID = "user-contrib-test-001"
CONTRIB_TYPE_URI = f"{DISC_NS}Vraag"
EVIDENCE_ID = "evidence-contrib-test-001"


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
async def thread_id(ds_id) -> str:
    """Maak een thread aan als fixture voor bijdrage-tests."""
    return await create_discussion_thread(TESSERA_ID, ds_id, USER_ID)


# ---------------------------------------------------------------------------
# create_thread_contribution
# ---------------------------------------------------------------------------

async def test_create_contribution_retourneert_contribution_id(ds_id, thread_id):
    contrib_id = await create_thread_contribution(
        thread_id=thread_id,
        design_space_id=ds_id,
        user_id=USER_ID,
        contribution_type_uri=CONTRIB_TYPE_URI,
        message_content="Dit is een testvraag.",
    )
    assert contrib_id, "contribution_id mag niet leeg zijn"
    assert len(contrib_id) == 36, "contribution_id moet een UUID zijn"


async def test_create_contribution_schrijft_type_triple(ds_id, thread_id):
    contrib_id = await create_thread_contribution(
        thread_id=thread_id,
        design_space_id=ds_id,
        user_id=USER_ID,
        contribution_type_uri=CONTRIB_TYPE_URI,
        message_content="Testvraag.",
    )
    contrib_uri = f"urn:valor:contrib:{contrib_id}"
    graph = named_graph_uri(ds_id)

    rows = await _sparql_select(graph, f"""
        PREFIX disc: <{DISC_NS}>
        SELECT ?contrib WHERE {{
          GRAPH <{graph}> {{
            <{contrib_uri}> a disc:ThreadContribution .
            BIND(<{contrib_uri}> AS ?contrib)
          }}
        }}
    """)
    assert rows, "disc:ThreadContribution-triple ontbreekt in Fuseki"


async def test_create_contribution_schrijft_contribution_type(ds_id, thread_id):
    contrib_id = await create_thread_contribution(
        thread_id=thread_id,
        design_space_id=ds_id,
        user_id=USER_ID,
        contribution_type_uri=CONTRIB_TYPE_URI,
        message_content="Testvraag.",
    )
    contrib_uri = f"urn:valor:contrib:{contrib_id}"
    graph = named_graph_uri(ds_id)

    rows = await _sparql_select(graph, f"""
        PREFIX disc: <{DISC_NS}>
        SELECT ?type WHERE {{
          GRAPH <{graph}> {{
            <{contrib_uri}> disc:contributionType ?type .
          }}
        }}
    """)
    assert rows, "disc:contributionType ontbreekt"
    assert rows[0]["type"]["value"] == CONTRIB_TYPE_URI


async def test_create_contribution_schrijft_prov_triples(ds_id, thread_id):
    contrib_id = await create_thread_contribution(
        thread_id=thread_id,
        design_space_id=ds_id,
        user_id=USER_ID,
        contribution_type_uri=CONTRIB_TYPE_URI,
        message_content="Testvraag.",
    )
    contrib_uri = f"urn:valor:contrib:{contrib_id}"
    user_uri = f"urn:valor:user:{USER_ID}"
    graph = named_graph_uri(ds_id)

    rows = await _sparql_select(graph, f"""
        PREFIX prov: <{PROV_NS}>
        SELECT ?associated_with ?ended_at WHERE {{
          GRAPH <{graph}> {{
            <{contrib_uri}> prov:wasAssociatedWith ?associated_with ;
                             prov:endedAtTime ?ended_at .
          }}
        }}
    """)
    assert rows, "prov:wasAssociatedWith / prov:endedAtTime ontbreken"
    assert rows[0]["associated_with"]["value"] == user_uri
    assert rows[0]["ended_at"]["value"], "endedAtTime mag niet leeg zijn"


async def test_create_contribution_koppelt_aan_thread(ds_id, thread_id):
    contrib_id = await create_thread_contribution(
        thread_id=thread_id,
        design_space_id=ds_id,
        user_id=USER_ID,
        contribution_type_uri=CONTRIB_TYPE_URI,
        message_content="Testvraag.",
    )
    contrib_uri = f"urn:valor:contrib:{contrib_id}"
    thread_uri = f"urn:valor:thread:{thread_id}"
    graph = named_graph_uri(ds_id)

    rows = await _sparql_select(graph, f"""
        PREFIX disc: <{DISC_NS}>
        SELECT ?contrib WHERE {{
          GRAPH <{graph}> {{
            <{thread_uri}> disc:hasContribution <{contrib_uri}> .
            BIND(<{contrib_uri}> AS ?contrib)
          }}
        }}
    """)
    assert rows, "disc:hasContribution-koppeling ontbreekt"


async def test_create_contribution_met_evidence(ds_id, thread_id):
    contrib_id = await create_thread_contribution(
        thread_id=thread_id,
        design_space_id=ds_id,
        user_id=USER_ID,
        contribution_type_uri=f"{DISC_NS}Bewijs",
        message_content="Bewijs voor de stelling.",
        evidence_id=EVIDENCE_ID,
    )
    contrib_uri = f"urn:valor:contrib:{contrib_id}"
    evidence_uri = f"urn:valor:evidence:{EVIDENCE_ID}"
    graph = named_graph_uri(ds_id)

    rows = await _sparql_select(graph, f"""
        PREFIX disc: <{DISC_NS}>
        SELECT ?evidence WHERE {{
          GRAPH <{graph}> {{
            <{contrib_uri}> disc:attachesEvidence ?evidence .
          }}
        }}
    """)
    assert rows, "disc:attachesEvidence-triple ontbreekt"
    assert rows[0]["evidence"]["value"] == evidence_uri


async def test_create_contribution_zonder_evidence_geen_attaches_triple(ds_id, thread_id):
    contrib_id = await create_thread_contribution(
        thread_id=thread_id,
        design_space_id=ds_id,
        user_id=USER_ID,
        contribution_type_uri=CONTRIB_TYPE_URI,
        message_content="Testvraag zonder bewijs.",
    )
    contrib_uri = f"urn:valor:contrib:{contrib_id}"
    graph = named_graph_uri(ds_id)

    rows = await _sparql_select(graph, f"""
        PREFIX disc: <{DISC_NS}>
        SELECT ?evidence WHERE {{
          GRAPH <{graph}> {{
            <{contrib_uri}> disc:attachesEvidence ?evidence .
          }}
        }}
    """)
    assert rows == [], "disc:attachesEvidence mag niet aanwezig zijn zonder evidence_id"


# ---------------------------------------------------------------------------
# get_contributions_by_thread
# ---------------------------------------------------------------------------

async def test_get_contributions_retourneert_lege_lijst(ds_id, thread_id):
    result = await get_contributions_by_thread(thread_id, ds_id)
    assert result == []


async def test_get_contributions_retourneert_bijdrage(ds_id, thread_id):
    contrib_id = await create_thread_contribution(
        thread_id=thread_id,
        design_space_id=ds_id,
        user_id=USER_ID,
        contribution_type_uri=CONTRIB_TYPE_URI,
        message_content="Testvraag.",
    )
    result = await get_contributions_by_thread(thread_id, ds_id)

    assert len(result) == 1
    assert result[0]["contribution_id"] == contrib_id
    assert result[0]["thread_id"] == thread_id
    assert result[0]["contributed_by"] == f"urn:valor:user:{USER_ID}"
    assert result[0]["evidence_id"] is None


async def test_get_contributions_retourneert_meerdere_bijdragen_gesorteerd(ds_id, thread_id):
    cid1 = await create_thread_contribution(
        thread_id=thread_id,
        design_space_id=ds_id,
        user_id=USER_ID,
        contribution_type_uri=CONTRIB_TYPE_URI,
        message_content="Eerste bijdrage.",
    )
    cid2 = await create_thread_contribution(
        thread_id=thread_id,
        design_space_id=ds_id,
        user_id=USER_ID,
        contribution_type_uri=f"{DISC_NS}Stelling",
        message_content="Tweede bijdrage.",
    )
    result = await get_contributions_by_thread(thread_id, ds_id)

    assert len(result) == 2
    contrib_ids = [r["contribution_id"] for r in result]
    assert cid1 in contrib_ids
    assert cid2 in contrib_ids
    # Gesorteerd op tijd: eerste bijdrage eerst
    assert contrib_ids.index(cid1) < contrib_ids.index(cid2)


async def test_get_contributions_met_evidence_id(ds_id, thread_id):
    contrib_id = await create_thread_contribution(
        thread_id=thread_id,
        design_space_id=ds_id,
        user_id=USER_ID,
        contribution_type_uri=f"{DISC_NS}Bewijs",
        message_content="Met bewijs.",
        evidence_id=EVIDENCE_ID,
    )
    result = await get_contributions_by_thread(thread_id, ds_id)

    assert len(result) == 1
    assert result[0]["evidence_id"] == EVIDENCE_ID
