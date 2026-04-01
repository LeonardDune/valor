"""Integratietests voor app.db.fuseki_socia (US-AI.5).

Test:
- assign_actor_role: schrijft socia:playsRole naar baseline-graph; idempotent
- get_actor_roles_in_ds: retourneert juiste actor-rol-paren
- get_tesserae_for_agent: vindt Tesserae waar valor:claimedBy = entity_uri
- get_designspaces_for_agent: vindt alle DSes waar agent een playsRole heeft

Gebruik:
    cd backend
    FUSEKI_URL=http://localhost:3030 pytest tests/integration/test_socia.py -v
"""
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

pytestmark = pytest.mark.integration

_SOCIA_NS = "https://valor-ecosystem.nl/ontology/socia#"
_VALOR_NS = "https://valor-ecosystem.nl/ontology/"
_ENTITIES_GRAPH = "urn:valor:entities"

TEST_DS_ID = "test-ds-socia"
TEST_DS_ID_2 = "test-ds-socia-2"
TEST_ENTITY_URI = "urn:valor:entities:person:socia-test-001"
TEST_ROLE_URI = f"{_SOCIA_NS}Implementer"
TEST_ROLE_URI_2 = f"{_SOCIA_NS}Supervisor"


def _baseline_graph(ds_id: str) -> str:
    return f"urn:valor:ds:{ds_id}/baseline"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _insert_triple(graph_uri: str, s: str, p: str, o: str, literal: bool = False) -> None:
    """Voegt een triple in via sparql_update. Gebruik literal=True voor string-literals als object."""
    from app.services.fuseki import sparql_update

    o_str = f'"{o}"' if literal else f"<{o}>"
    update = f"""
        INSERT DATA {{
          GRAPH <{graph_uri}> {{
            <{s}> <{p}> {o_str} .
          }}
        }}
    """
    await sparql_update(update, "test-helper")


async def _count_triples_in_graph(graph_uri: str, s: str, p: str, o: str) -> int:
    """Telt triples die overeenkomen met het patroon in de opgegeven graph."""
    from app.services.fuseki import sparql_select_global

    rows = await sparql_select_global(f"""
        SELECT (COUNT(*) AS ?c) WHERE {{
          GRAPH <{graph_uri}> {{
            <{s}> <{p}> <{o}> .
          }}
        }}
    """)
    return int(rows[0]["c"]) if rows else 0


# ---------------------------------------------------------------------------
# assign_actor_role
# ---------------------------------------------------------------------------

async def test_assign_actor_role_schrijft_plays_role_triple():
    from app.db.fuseki_socia import assign_actor_role

    await assign_actor_role(TEST_ENTITY_URI, TEST_ROLE_URI, TEST_DS_ID)

    count = await _count_triples_in_graph(
        _baseline_graph(TEST_DS_ID),
        TEST_ENTITY_URI,
        f"{_SOCIA_NS}playsRole",
        TEST_ROLE_URI,
    )
    assert count == 1


async def test_assign_actor_role_schrijft_is_stakeholder_in():
    from app.db.fuseki_socia import assign_actor_role

    await assign_actor_role(TEST_ENTITY_URI, TEST_ROLE_URI, TEST_DS_ID)

    count = await _count_triples_in_graph(
        _baseline_graph(TEST_DS_ID),
        TEST_ENTITY_URI,
        f"{_SOCIA_NS}isStakeholderIn",
        f"urn:valor:ds:{TEST_DS_ID}",
    )
    assert count == 1


async def test_assign_actor_role_idempotent():
    from app.db.fuseki_socia import assign_actor_role

    await assign_actor_role(TEST_ENTITY_URI, TEST_ROLE_URI, TEST_DS_ID)
    await assign_actor_role(TEST_ENTITY_URI, TEST_ROLE_URI, TEST_DS_ID)

    count = await _count_triples_in_graph(
        _baseline_graph(TEST_DS_ID),
        TEST_ENTITY_URI,
        f"{_SOCIA_NS}playsRole",
        TEST_ROLE_URI,
    )
    assert count == 1


async def test_assign_actor_role_meerdere_rollen_mogelijk():
    from app.db.fuseki_socia import assign_actor_role

    await assign_actor_role(TEST_ENTITY_URI, TEST_ROLE_URI, TEST_DS_ID)
    await assign_actor_role(TEST_ENTITY_URI, TEST_ROLE_URI_2, TEST_DS_ID)

    count1 = await _count_triples_in_graph(
        _baseline_graph(TEST_DS_ID),
        TEST_ENTITY_URI,
        f"{_SOCIA_NS}playsRole",
        TEST_ROLE_URI,
    )
    count2 = await _count_triples_in_graph(
        _baseline_graph(TEST_DS_ID),
        TEST_ENTITY_URI,
        f"{_SOCIA_NS}playsRole",
        TEST_ROLE_URI_2,
    )
    assert count1 == 1
    assert count2 == 1


# ---------------------------------------------------------------------------
# get_actor_roles_in_ds
# ---------------------------------------------------------------------------

async def test_get_actor_roles_in_ds_retourneert_rol_paar():
    from app.db.fuseki_socia import assign_actor_role, get_actor_roles_in_ds

    await assign_actor_role(TEST_ENTITY_URI, TEST_ROLE_URI, TEST_DS_ID)

    roles = await get_actor_roles_in_ds(TEST_DS_ID)

    assert len(roles) == 1
    assert roles[0]["entity_uri"] == TEST_ENTITY_URI
    assert roles[0]["role_uri"] == TEST_ROLE_URI


async def test_get_actor_roles_in_ds_bevat_role_local():
    from app.db.fuseki_socia import assign_actor_role, get_actor_roles_in_ds

    await assign_actor_role(TEST_ENTITY_URI, TEST_ROLE_URI, TEST_DS_ID)

    roles = await get_actor_roles_in_ds(TEST_DS_ID)

    assert roles[0]["role_local"] == "Implementer"


async def test_get_actor_roles_in_ds_join_entity_registry():
    from app.db.fuseki_socia import assign_actor_role, get_actor_roles_in_ds
    from app.ontology import UFOC_NS

    # Entiteit aanmaken in Entity Registry
    type_uri = f"{UFOC_NS}PhysicalAgent"
    await _insert_triple(_ENTITIES_GRAPH, TEST_ENTITY_URI, "http://www.w3.org/1999/02/22-rdf-syntax-ns#type", type_uri)
    await _insert_triple(_ENTITIES_GRAPH, TEST_ENTITY_URI, "http://www.w3.org/2000/01/rdf-schema#label", "Test Persoon", literal=True)
    await assign_actor_role(TEST_ENTITY_URI, TEST_ROLE_URI, TEST_DS_ID)

    roles = await get_actor_roles_in_ds(TEST_DS_ID)

    match = next((r for r in roles if r["entity_uri"] == TEST_ENTITY_URI), None)
    assert match is not None
    assert match["entity_type"] == type_uri
    assert match["entity_type_local"] == "PhysicalAgent"


async def test_get_actor_roles_in_ds_leeg_resultaat():
    from app.db.fuseki_socia import get_actor_roles_in_ds

    roles = await get_actor_roles_in_ds("ds-zonder-rollen")

    assert roles == []


async def test_get_actor_roles_in_ds_isoleert_per_ds():
    from app.db.fuseki_socia import assign_actor_role, get_actor_roles_in_ds

    await assign_actor_role(TEST_ENTITY_URI, TEST_ROLE_URI, TEST_DS_ID)

    roles_andere_ds = await get_actor_roles_in_ds(TEST_DS_ID_2)

    assert roles_andere_ds == []


# ---------------------------------------------------------------------------
# get_tesserae_for_agent
# ---------------------------------------------------------------------------

async def test_get_tesserae_for_agent_vindt_tessera():
    from app.db.fuseki_socia import get_tesserae_for_agent

    tessera_uri = "urn:valor:tessera:socia-test-factor-001"
    graph = _baseline_graph(TEST_DS_ID)

    await _insert_triple(graph, tessera_uri, f"{_VALOR_NS}claimedBy", TEST_ENTITY_URI)

    results = await get_tesserae_for_agent(TEST_ENTITY_URI, TEST_DS_ID)

    assert len(results) == 1
    assert results[0]["tessera_uri"] == tessera_uri
    assert results[0]["graph"] == graph


async def test_get_tesserae_for_agent_bevat_type_en_content():
    from app.db.fuseki_socia import get_tesserae_for_agent
    from app.services.fuseki import sparql_update

    tessera_uri = "urn:valor:tessera:socia-test-factor-002"
    type_uri = f"{_VALOR_NS}Factor"
    graph = _baseline_graph(TEST_DS_ID)

    update = f"""
        INSERT DATA {{
          GRAPH <{graph}> {{
            <{tessera_uri}> <{_VALOR_NS}claimedBy> <{TEST_ENTITY_URI}> ;
                            <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <{type_uri}> ;
                            <{_VALOR_NS}claimContent> "Testinhoud" .
          }}
        }}
    """
    await sparql_update(update, "test-helper")

    results = await get_tesserae_for_agent(TEST_ENTITY_URI, TEST_DS_ID)

    match = next((r for r in results if r["tessera_uri"] == tessera_uri), None)
    assert match is not None
    assert match["type"] == type_uri
    assert match["type_local"] == "Factor"
    assert match["content"] == "Testinhoud"


async def test_get_tesserae_for_agent_leeg_resultaat():
    from app.db.fuseki_socia import get_tesserae_for_agent

    results = await get_tesserae_for_agent("urn:valor:entities:person:bestaat-niet", TEST_DS_ID)

    assert results == []


async def test_get_tesserae_for_agent_isoleert_per_ds():
    from app.db.fuseki_socia import get_tesserae_for_agent

    tessera_uri = "urn:valor:tessera:socia-test-factor-003"
    graph_andere_ds = _baseline_graph(TEST_DS_ID_2)

    await _insert_triple(graph_andere_ds, tessera_uri, f"{_VALOR_NS}claimedBy", TEST_ENTITY_URI)

    # DS2-tessera mag NIET zichtbaar zijn via DS1-query
    results = await get_tesserae_for_agent(TEST_ENTITY_URI, TEST_DS_ID)
    uris = [r["tessera_uri"] for r in results]
    assert tessera_uri not in uris


# ---------------------------------------------------------------------------
# get_designspaces_for_agent
# ---------------------------------------------------------------------------

async def test_get_designspaces_for_agent_retourneert_ds_id():
    from app.db.fuseki_socia import assign_actor_role, get_designspaces_for_agent

    await assign_actor_role(TEST_ENTITY_URI, TEST_ROLE_URI, TEST_DS_ID)

    ds_ids = await get_designspaces_for_agent(TEST_ENTITY_URI)

    assert TEST_DS_ID in ds_ids


async def test_get_designspaces_for_agent_meerdere_ds():
    from app.db.fuseki_socia import assign_actor_role, get_designspaces_for_agent

    await assign_actor_role(TEST_ENTITY_URI, TEST_ROLE_URI, TEST_DS_ID)
    await assign_actor_role(TEST_ENTITY_URI, TEST_ROLE_URI_2, TEST_DS_ID_2)

    ds_ids = await get_designspaces_for_agent(TEST_ENTITY_URI)

    assert TEST_DS_ID in ds_ids
    assert TEST_DS_ID_2 in ds_ids


async def test_get_designspaces_for_agent_leeg_resultaat():
    from app.db.fuseki_socia import get_designspaces_for_agent

    ds_ids = await get_designspaces_for_agent("urn:valor:entities:person:bestaat-niet")

    assert ds_ids == []


async def test_get_designspaces_for_agent_geen_duplicaten():
    from app.db.fuseki_socia import assign_actor_role, get_designspaces_for_agent

    # Twee rollen in dezelfde DS — DISTINCT moet zorgen voor één DS-ID
    await assign_actor_role(TEST_ENTITY_URI, TEST_ROLE_URI, TEST_DS_ID)
    await assign_actor_role(TEST_ENTITY_URI, TEST_ROLE_URI_2, TEST_DS_ID)

    ds_ids = await get_designspaces_for_agent(TEST_ENTITY_URI)

    assert ds_ids.count(TEST_DS_ID) == 1
