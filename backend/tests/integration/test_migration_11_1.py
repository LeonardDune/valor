"""Integratietests voor US-11.1: verificatie- en repairlogica Neo4j → Fuseki Tesserae.

Test de kernfuncties van verify_migration_11_1.py zonder Neo4j — de Neo4j-laag
wordt vervangen door helper-functies die testdata injecteren.

Vereisten:
  - Fuseki draait op FUSEKI_URL (default: http://localhost:3030)
  - conftest.py heeft de 'valor-test' dataset aangemaakt

Gebruik:
    cd backend
    FUSEKI_URL=http://localhost:3030 pytest tests/integration/test_migration_11_1.py -v
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.ontology import VALOR_NS

pytestmark = pytest.mark.integration

TESSERA_TYPE = f"{VALOR_NS}Tessera"
XSD_NS = "http://www.w3.org/2001/XMLSchema#"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _sparql_select_in_graph(graph_uri: str, sparql: str) -> list[dict]:
    """Voer een SPARQL SELECT uit in een specifieke named graph."""
    import httpx
    from tests.conftest import FUSEKI_TEST_URL, FUSEKI_TEST_DATASET

    endpoint = f"{FUSEKI_TEST_URL}/{FUSEKI_TEST_DATASET}/sparql"
    async with httpx.AsyncClient() as client:
        r = await client.post(
            endpoint,
            data={"query": sparql},
            headers={"Accept": "application/sparql-results+json"},
            timeout=15,
        )
    r.raise_for_status()
    return r.json()["results"]["bindings"]


async def _seed_tessera(ds_id: str, tessera_id: str, content: str = "Testinhoud") -> None:
    """Voeg een valor:Tessera in in de asis-graph van een DesignSpace."""
    from app.services.fuseki import sparql_update, initialize_design_space_graphs

    issue_uri = f"urn:valor:issue:{ds_id}"
    await initialize_design_space_graphs(ds_id, issue_uri)

    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    asis_graph = f"urn:valor:ds:{ds_id}/asis"
    escaped = content.replace('"', '\\"')

    await sparql_update(
        f"""INSERT DATA {{
  GRAPH <{asis_graph}> {{
    <{tessera_uri}> a <{VALOR_NS}Tessera> ;
      <{VALOR_NS}claimContent> "{escaped}"@nl ;
      <{VALOR_NS}inDesignSpace> <urn:valor:ds:{ds_id}> .
  }}
}}""",
        ds_id,
    )


async def _count_tesserae_in_graph(ds_id: str) -> int:
    """Telt valor:Tessera resources in de asis-graph van een DesignSpace."""
    asis_graph = f"urn:valor:ds:{ds_id}/asis"
    rows = await _sparql_select_in_graph(
        asis_graph,
        f"SELECT (COUNT(?t) AS ?count) WHERE {{ GRAPH <{asis_graph}> {{ ?t a <{TESSERA_TYPE}> }} }}",
    )
    return int(rows[0]["count"]["value"]) if rows else 0


# ---------------------------------------------------------------------------
# Tests: _count_fuseki_tesserae
# ---------------------------------------------------------------------------

async def test_count_fuseki_tesserae_lege_graph(ds_id):
    """Een DesignSpace zonder Tesserae telt 0."""
    from scripts.verify_migration_11_1 import _count_fuseki_tesserae
    from app.services.fuseki import initialize_design_space_graphs

    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")
    count = await _count_fuseki_tesserae(ds_id)
    assert count == 0


async def test_count_fuseki_tesserae_met_data(ds_id):
    """Na inzaaien van 2 Tesserae telt de functie er 2."""
    from scripts.verify_migration_11_1 import _count_fuseki_tesserae

    await _seed_tessera(ds_id, "factor-aaa")
    await _seed_tessera(ds_id, "factor-bbb")

    count = await _count_fuseki_tesserae(ds_id)
    assert count == 2


# ---------------------------------------------------------------------------
# Tests: _get_fuseki_tessera_uris
# ---------------------------------------------------------------------------

async def test_get_fuseki_tessera_uris_geeft_correcte_uris(ds_id):
    """De URIs van aanwezige Tesserae worden correct teruggegeven."""
    from scripts.verify_migration_11_1 import _get_fuseki_tessera_uris

    await _seed_tessera(ds_id, "factor-xyz")
    uris = await _get_fuseki_tessera_uris(ds_id)

    assert f"urn:valor:tessera:factor-xyz" in uris


# ---------------------------------------------------------------------------
# Tests: _insert_tessera_if_absent
# ---------------------------------------------------------------------------

async def test_insert_tessera_if_absent_voegt_in(ds_id):
    """Een nieuwe Tessera wordt ingevoegd."""
    from scripts.verify_migration_11_1 import _insert_tessera_if_absent
    from app.services.fuseki import initialize_design_space_graphs

    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")

    tessera_uri = f"urn:valor:tessera:new-factor-001"
    await _insert_tessera_if_absent(
        ds_id=ds_id,
        tessera_uri=tessera_uri,
        content="Nieuwe factor",
        creator_uri="urn:valor:user:test-user",
        created_at="2026-01-01T00:00:00+00:00",
    )

    count = await _count_tesserae_in_graph(ds_id)
    assert count == 1


async def test_insert_tessera_if_absent_is_idempotent(ds_id):
    """Twee keer dezelfde Tessera invoegen resulteert in slechts 1 resource."""
    from scripts.verify_migration_11_1 import _insert_tessera_if_absent
    from app.services.fuseki import initialize_design_space_graphs

    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")
    tessera_uri = f"urn:valor:tessera:idempotent-factor"

    await _insert_tessera_if_absent(
        ds_id=ds_id,
        tessera_uri=tessera_uri,
        content="Factor naam",
        creator_uri="urn:valor:user:test-user",
        created_at="2026-01-01T00:00:00+00:00",
    )
    await _insert_tessera_if_absent(
        ds_id=ds_id,
        tessera_uri=tessera_uri,
        content="Factor naam",
        creator_uri="urn:valor:user:test-user",
        created_at="2026-01-01T00:00:00+00:00",
    )

    count = await _count_tesserae_in_graph(ds_id)
    assert count == 1


# ---------------------------------------------------------------------------
# Tests: verify_design_space (end-to-end verificatielogica)
# ---------------------------------------------------------------------------

async def test_verify_design_space_checksum_ok(ds_id):
    """Verificatie slaagt als alle Neo4j-resources als Tessera in Fuseki aanwezig zijn."""
    from scripts.verify_migration_11_1 import verify_design_space

    # Seed 1 factor + 1 claim in Fuseki
    await _seed_tessera(ds_id, "fac-001")
    await _seed_tessera(ds_id, "clm-001")

    # Fake version-dict (Neo4j) met dezelfde IDs
    version = {
        "version_id": "version-test-001",
        "version_name": "Testversie",
        "ds_id": ds_id,
        "theme_creator": "test-user",
    }

    # Monkey-patch Neo4j-aanroepen
    import scripts.verify_migration_11_1 as mod

    original_factors = mod._get_neo4j_factors
    original_claims = mod._get_neo4j_claims
    mod._get_neo4j_factors = lambda driver, vid: [
        {"id": "fac-001", "name": "Factor A", "description": "", "role": "middel", "created_at": "2026-01-01T00:00:00"},
    ]
    mod._get_neo4j_claims = lambda driver, vid: [
        {
            "id": "clm-001", "statement": "A veroorzaakt B", "polarity": "+",
            "confidence": 0.8, "evidence_text": "",
            "source_version_id": "fac-001", "target_version_id": "fac-001",
            "created_at": "2026-01-01T00:00:00",
        },
    ]

    try:
        result = await verify_design_space(version, driver=None, repair=False, dry_run=False)
    finally:
        mod._get_neo4j_factors = original_factors
        mod._get_neo4j_claims = original_claims

    assert result["checksum_ok"] is True
    assert result["status"] == "ok"
    assert result["missing_factors"] == []
    assert result["missing_claims"] == []


async def test_verify_design_space_detecteert_missing_tessera(ds_id):
    """Verificatie detecteert een ontbrekende factor-Tessera."""
    from scripts.verify_migration_11_1 import verify_design_space

    # Alleen factor fac-002 aanwezig, fac-001 ontbreekt
    await _seed_tessera(ds_id, "fac-002")

    version = {
        "version_id": "version-test-002",
        "version_name": "Testversie",
        "ds_id": ds_id,
        "theme_creator": "test-user",
    }

    import scripts.verify_migration_11_1 as mod
    original_factors = mod._get_neo4j_factors
    original_claims = mod._get_neo4j_claims
    mod._get_neo4j_factors = lambda driver, vid: [
        {"id": "fac-001", "name": "Factor A", "description": "", "role": "middel", "created_at": "2026-01-01T00:00:00"},
        {"id": "fac-002", "name": "Factor B", "description": "", "role": "criterium", "created_at": "2026-01-01T00:00:00"},
    ]
    mod._get_neo4j_claims = lambda driver, vid: []

    try:
        result = await verify_design_space(version, driver=None, repair=False, dry_run=False)
    finally:
        mod._get_neo4j_factors = original_factors
        mod._get_neo4j_claims = original_claims

    assert result["checksum_ok"] is False
    assert result["status"] == "mismatch"
    assert "fac-001" in result["missing_factors"]
    assert "fac-002" not in result["missing_factors"]


async def test_verify_design_space_repair_vult_ontbrekende_tessera_in(ds_id):
    """Repair-mode voegt een ontbrekende Tessera in en herstelt de checksum."""
    from scripts.verify_migration_11_1 import verify_design_space
    from app.services.fuseki import initialize_design_space_graphs

    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")

    version = {
        "version_id": "version-test-003",
        "version_name": "Repairversie",
        "ds_id": ds_id,
        "theme_creator": "test-user",
    }

    import scripts.verify_migration_11_1 as mod
    original_factors = mod._get_neo4j_factors
    original_claims = mod._get_neo4j_claims
    mod._get_neo4j_factors = lambda driver, vid: [
        {"id": "fac-repair-001", "name": "Repairfactor", "description": "Test", "role": "middel", "created_at": "2026-01-01T00:00:00"},
    ]
    mod._get_neo4j_claims = lambda driver, vid: []

    try:
        result = await verify_design_space(version, driver=None, repair=True, dry_run=False)
    finally:
        mod._get_neo4j_factors = original_factors
        mod._get_neo4j_claims = original_claims

    assert result["status"] == "repaired"
    assert result["checksum_ok"] is True
    assert result["repaired_factors"] == 1

    # Verificeer werkelijk aanwezig in Fuseki
    count = await _count_tesserae_in_graph(ds_id)
    assert count == 1


async def test_verify_design_space_geen_designspace(ds_id):
    """Een ThemeVersion zonder DesignSpace wordt overgeslagen."""
    from scripts.verify_migration_11_1 import verify_design_space

    version = {
        "version_id": "version-no-ds",
        "version_name": "Geen DS",
        "ds_id": None,
        "theme_creator": "test-user",
    }

    result = await verify_design_space(version, driver=None, repair=False, dry_run=False)
    assert result["status"] == "no_designspace"
