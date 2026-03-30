"""Integratietests voor app.db.fuseki_entities (US-AI.3).

Test de Entity Registry: named graph urn:valor:entities, JIT-bridge,
CRUD-operaties en rol-assignaties.

Gebruik:
    cd backend
    FUSEKI_URL=http://localhost:3030 pytest tests/integration/test_entities.py -v
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

pytestmark = pytest.mark.integration

_ENTITIES_GRAPH = "urn:valor:entities"
TEST_SUPABASE_ID = "test-supabase-uuid-0001"
TEST_DS_ID = "test-ds-entities"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _count_entities(entity_type_uri: str) -> int:
    from app.services.fuseki import sparql_select_global
    rows = await sparql_select_global(
        f"SELECT (COUNT(?e) AS ?c) WHERE {{ GRAPH <{_ENTITIES_GRAPH}> {{ ?e a <{entity_type_uri}> }} }}"
    )
    return int(rows[0]["c"]) if rows else 0


# ---------------------------------------------------------------------------
# JIT-bridge: ensure_person_entity
# ---------------------------------------------------------------------------

async def test_ensure_person_entity_maakt_physical_agent_aan():
    from app.db.fuseki_entities import ensure_person_entity
    from app.ontology import UFOC_NS

    uri = await ensure_person_entity(TEST_SUPABASE_ID, "Test Gebruiker")

    assert uri == f"{_ENTITIES_GRAPH}:person:{TEST_SUPABASE_ID}"
    count = await _count_entities(f"{UFOC_NS}PhysicalAgent")
    assert count == 1


async def test_ensure_person_entity_idempotent():
    from app.db.fuseki_entities import ensure_person_entity
    from app.ontology import UFOC_NS

    uri1 = await ensure_person_entity(TEST_SUPABASE_ID, "Test Gebruiker")
    uri2 = await ensure_person_entity(TEST_SUPABASE_ID, "Test Gebruiker")

    assert uri1 == uri2
    count = await _count_entities(f"{UFOC_NS}PhysicalAgent")
    assert count == 1  # geen duplicaat


async def test_ensure_person_entity_zonder_naam():
    from app.db.fuseki_entities import ensure_person_entity
    from app.ontology import UFOC_NS

    uri = await ensure_person_entity(TEST_SUPABASE_ID)

    assert uri is not None
    count = await _count_entities(f"{UFOC_NS}PhysicalAgent")
    assert count == 1


# ---------------------------------------------------------------------------
# create_entity
# ---------------------------------------------------------------------------

async def test_create_entity_physical_agent():
    from app.db.fuseki_entities import create_entity
    from app.ontology import UFOC_NS

    uri = await create_entity("PhysicalAgent", "Jan de Vries")

    assert "urn:valor:entities:person:" in uri
    count = await _count_entities(f"{UFOC_NS}PhysicalAgent")
    assert count == 1


async def test_create_entity_institutional_agent():
    from app.db.fuseki_entities import create_entity
    from app.ontology import UFOC_NS

    uri = await create_entity("InstitutionalAgent", "Gemeente Amsterdam")

    assert "urn:valor:entities:org:" in uri
    count = await _count_entities(f"{UFOC_NS}InstitutionalAgent")
    assert count == 1


async def test_create_entity_normative_description():
    from app.db.fuseki_entities import create_entity
    from app.ontology import UFOC_NS

    uri = await create_entity(
        "NormativeDescription",
        "Wet op de schuldsanering",
        identifier="wsnp-2024",
    )

    assert uri == "urn:valor:entities:norm:wsnp-2024"
    count = await _count_entities(f"{UFOC_NS}NormativeDescription")
    assert count == 1


async def test_create_entity_onbekend_type_geeft_error():
    from app.db.fuseki_entities import create_entity

    with pytest.raises(ValueError, match="Onbekend entity type"):
        await create_entity("OnbestaandType", "Test")


async def test_create_entity_met_properties():
    from app.db.fuseki_entities import create_entity, get_entity

    uri = await create_entity(
        "InstitutionalAgent",
        "Ministerie van SZW",
        properties={"kvkNumber": "12345678"},
    )
    entity = await get_entity(uri)
    assert entity is not None
    assert entity["label"] == "Ministerie van SZW"


# ---------------------------------------------------------------------------
# get_entity
# ---------------------------------------------------------------------------

async def test_get_entity_retourneert_data():
    from app.db.fuseki_entities import create_entity, get_entity

    uri = await create_entity("PhysicalAgent", "Piet Jansen")
    entity = await get_entity(uri)

    assert entity is not None
    assert entity["uri"] == uri
    assert entity["entity_type"] == "PhysicalAgent"
    assert entity["label"] == "Piet Jansen"


async def test_get_entity_niet_bestaand_geeft_none():
    from app.db.fuseki_entities import get_entity

    result = await get_entity("urn:valor:entities:person:bestaat-niet")
    assert result is None


# ---------------------------------------------------------------------------
# search_entities
# ---------------------------------------------------------------------------

async def test_search_entities_vindt_op_label():
    from app.db.fuseki_entities import create_entity, search_entities

    await create_entity("PhysicalAgent", "Maria van Dijk")
    await create_entity("PhysicalAgent", "Johan van Dijk")
    await create_entity("InstitutionalAgent", "Gemeente Rotterdam")

    results = await search_entities("van dijk")
    assert len(results) == 2
    labels = [r["label"] for r in results]
    assert "Maria van Dijk" in labels
    assert "Johan van Dijk" in labels


async def test_search_entities_filter_op_type():
    from app.db.fuseki_entities import create_entity, search_entities

    await create_entity("PhysicalAgent", "Maria Gemeente")
    await create_entity("InstitutionalAgent", "Gemeente Alkmaar")

    results = await search_entities("gemeente", entity_type="InstitutionalAgent")
    assert len(results) == 1
    assert results[0]["entity_type"] == "InstitutionalAgent"


async def test_search_entities_leeg_resultaat():
    from app.db.fuseki_entities import search_entities

    results = await search_entities("xyzOnbestaandeNaam")
    assert results == []


# ---------------------------------------------------------------------------
# assign_role + get_roles_for_entity
# ---------------------------------------------------------------------------

async def test_assign_role_en_ophalen():
    from app.db.fuseki_entities import assign_role, create_entity, get_roles_for_entity

    uri = await create_entity("InstitutionalAgent", "Gemeente Utrecht")
    role_uri = "https://valor-ecosystem.nl/ontology/socia#Implementer"

    await assign_role(uri, role_uri, TEST_DS_ID, context="Schuldhulpverlening")
    roles = await get_roles_for_entity(uri, TEST_DS_ID)

    assert len(roles) == 1
    assert roles[0]["role_uri"] == role_uri
    assert roles[0]["context"] == "Schuldhulpverlening"


async def test_get_roles_voor_entity_zonder_rollen():
    from app.db.fuseki_entities import create_entity, get_roles_for_entity

    uri = await create_entity("PhysicalAgent", "Anonieme Gebruiker")
    roles = await get_roles_for_entity(uri, TEST_DS_ID)

    assert roles == []


async def test_meerdere_rollen_per_entiteit():
    from app.db.fuseki_entities import assign_role, create_entity, get_roles_for_entity

    uri = await create_entity("InstitutionalAgent", "Belastingdienst")
    role1 = "https://valor-ecosystem.nl/ontology/socia#Supervisor"
    role2 = "https://valor-ecosystem.nl/ontology/socia#ChainPartner"

    await assign_role(uri, role1, TEST_DS_ID)
    await assign_role(uri, role2, TEST_DS_ID)

    roles = await get_roles_for_entity(uri, TEST_DS_ID)
    role_uris = [r["role_uri"] for r in roles]
    assert role1 in role_uris
    assert role2 in role_uris
