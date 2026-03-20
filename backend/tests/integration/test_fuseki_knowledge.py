"""Integratietests voor app.db.fuseki_knowledge (US-11.2).

Test de SPARQL-gebaseerde lees- en schrijfoperaties voor Factors en Claims.
Neo4j-aanroepen zijn gemonkey-patched — alleen Fuseki is vereist.

Gebruik:
    cd backend
    FUSEKI_URL=http://localhost:3030 pytest tests/integration/test_fuseki_knowledge.py -v
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.ontology import VALOR_NS

pytestmark = pytest.mark.integration

USER_ID = "user-test-001"
USER_URI = f"urn:valor:user:{USER_ID}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _seed_design_space(ds_id: str) -> None:
    """Initialiseert de asis-graph voor een test-DesignSpace."""
    from app.services.fuseki import initialize_design_space_graphs
    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")


async def _count_tesserae(ds_id: str) -> int:
    from app.services.fuseki import sparql_select_global
    graph = f"urn:valor:ds:{ds_id}/asis"
    rows = await sparql_select_global(
        f"SELECT (COUNT(?t) AS ?c) WHERE {{ GRAPH <{graph}> {{ ?t a <{VALOR_NS}Tessera> }} }}"
    )
    return int(rows[0]["c"]) if rows else 0


# ---------------------------------------------------------------------------
# Factor writes
# ---------------------------------------------------------------------------

async def test_create_factor_fuseki_maakt_tessera_aan(ds_id):
    await _seed_design_space(ds_id)
    from app.db.fuseki_knowledge import create_factor_fuseki

    base_id = await create_factor_fuseki(ds_id, "Factor Alpha", "middel", USER_ID)
    assert base_id

    count = await _count_tesserae(ds_id)
    assert count == 1


async def test_create_factor_fuseki_slaat_base_id_op(ds_id):
    await _seed_design_space(ds_id)
    from app.db.fuseki_knowledge import create_factor_fuseki
    from app.services.fuseki import sparql_select_global

    base_id = await create_factor_fuseki(ds_id, "Factor Beta", "criterium", USER_ID, description="Een criterium")

    graph = f"urn:valor:ds:{ds_id}/asis"
    rows = await sparql_select_global(
        f'SELECT ?bid WHERE {{ GRAPH <{graph}> {{ <urn:valor:tessera:{base_id}> <{VALOR_NS}baseId> ?bid }} }}'
    )
    assert rows, "valor:baseId niet gevonden"
    assert rows[0]["bid"] == base_id


async def test_update_factor_fuseki_wijzigt_naam(ds_id):
    await _seed_design_space(ds_id)
    from app.db.fuseki_knowledge import create_factor_fuseki, update_factor_fuseki
    from app.services.fuseki import sparql_select_global

    base_id = await create_factor_fuseki(ds_id, "Oude naam", "middel", USER_ID)
    await update_factor_fuseki(base_id, ds_id, name="Nieuwe naam")

    graph = f"urn:valor:ds:{ds_id}/asis"
    rows = await sparql_select_global(
        f'SELECT ?name WHERE {{ GRAPH <{graph}> {{ <urn:valor:tessera:{base_id}> <{VALOR_NS}claimContent> ?name }} }}'
    )
    assert any("Nieuwe naam" in r["name"] for r in rows), "Naam niet bijgewerkt"


async def test_delete_factor_fuseki_verwijdert_tessera(ds_id):
    await _seed_design_space(ds_id)
    from app.db.fuseki_knowledge import create_factor_fuseki, delete_factor_fuseki

    base_id = await create_factor_fuseki(ds_id, "Te verwijderen", "middel", USER_ID)
    assert await _count_tesserae(ds_id) == 1

    await delete_factor_fuseki(base_id, ds_id)
    assert await _count_tesserae(ds_id) == 0


# ---------------------------------------------------------------------------
# Factor reads (GET)
# ---------------------------------------------------------------------------

async def test_get_factors_voor_designspace_retourneert_factoren(ds_id):
    await _seed_design_space(ds_id)
    from app.db.fuseki_knowledge import create_factor_fuseki, _sparql_get_factors

    await create_factor_fuseki(ds_id, "Factor A", "middel", USER_ID)
    await create_factor_fuseki(ds_id, "Factor B", "criterium", USER_ID)

    factors = await _sparql_get_factors(ds_id)
    assert len(factors) == 2
    names = {f["name"] for f in factors}
    assert "Factor A" in names
    assert "Factor B" in names


async def test_get_factors_retourneert_base_id_als_id(ds_id):
    await _seed_design_space(ds_id)
    from app.db.fuseki_knowledge import create_factor_fuseki, _sparql_get_factors

    base_id = await create_factor_fuseki(ds_id, "Factor met ID", "middel", USER_ID)

    factors = await _sparql_get_factors(ds_id)
    assert len(factors) == 1
    assert factors[0]["id"] == base_id


async def test_get_factors_lege_designspace_geeft_lege_lijst(ds_id):
    await _seed_design_space(ds_id)
    from app.db.fuseki_knowledge import _sparql_get_factors

    factors = await _sparql_get_factors(ds_id)
    assert factors == []


# ---------------------------------------------------------------------------
# Claim writes
# ---------------------------------------------------------------------------

async def test_create_claim_fuseki_koppelt_factor_uris(ds_id):
    await _seed_design_space(ds_id)
    from app.db.fuseki_knowledge import create_factor_fuseki, create_claim_fuseki
    from app.services.fuseki import sparql_select_global

    fac_a = await create_factor_fuseki(ds_id, "Factor A", "middel", USER_ID)
    fac_b = await create_factor_fuseki(ds_id, "Factor B", "criterium", USER_ID)

    claim_id = await create_claim_fuseki(
        ds_id=ds_id,
        source_id=fac_a,
        target_id=fac_b,
        statement="A beïnvloedt B",
        polarity="+",
        user_id=USER_ID,
    )
    assert claim_id

    graph = f"urn:valor:ds:{ds_id}/asis"
    rows = await sparql_select_global(f"""
        SELECT ?from ?to WHERE {{
          GRAPH <{graph}> {{
            <urn:valor:tessera:{claim_id}> <{VALOR_NS}fromFactor> ?from ;
                                           <{VALOR_NS}toFactor> ?to .
          }}
        }}
    """)
    assert rows, "fromFactor/toFactor niet gevonden"
    assert f"urn:valor:tessera:{fac_a}" == rows[0]["from"]
    assert f"urn:valor:tessera:{fac_b}" == rows[0]["to"]


async def test_create_claim_fuseki_slaat_base_id_op(ds_id):
    await _seed_design_space(ds_id)
    from app.db.fuseki_knowledge import create_factor_fuseki, create_claim_fuseki
    from app.services.fuseki import sparql_select_global

    fac_a = await create_factor_fuseki(ds_id, "Bron", "middel", USER_ID)
    fac_b = await create_factor_fuseki(ds_id, "Doel", "middel", USER_ID)
    claim_id = await create_claim_fuseki(ds_id, fac_a, fac_b, "Stelling", "+", USER_ID)

    graph = f"urn:valor:ds:{ds_id}/asis"
    rows = await sparql_select_global(
        f'SELECT ?bid WHERE {{ GRAPH <{graph}> {{ <urn:valor:tessera:{claim_id}> <{VALOR_NS}baseId> ?bid }} }}'
    )
    assert rows
    assert rows[0]["bid"] == claim_id


# ---------------------------------------------------------------------------
# Claim reads (GET)
# ---------------------------------------------------------------------------

async def test_get_claims_voor_designspace_retourneert_claims(ds_id):
    await _seed_design_space(ds_id)
    from app.db.fuseki_knowledge import create_factor_fuseki, create_claim_fuseki, _sparql_get_claims

    fac_a = await create_factor_fuseki(ds_id, "Bron", "middel", USER_ID)
    fac_b = await create_factor_fuseki(ds_id, "Doel", "middel", USER_ID)
    await create_claim_fuseki(ds_id, fac_a, fac_b, "A veroorzaakt B", "+", USER_ID, confidence=0.8)

    claims = await _sparql_get_claims(ds_id)
    assert len(claims) == 1
    c = claims[0]
    assert c["statement"] == "A veroorzaakt B"
    assert c["polarity"] == "+"
    assert c["source_id"] == fac_a
    assert c["target_id"] == fac_b


async def test_get_claims_retourneert_base_id_als_id(ds_id):
    await _seed_design_space(ds_id)
    from app.db.fuseki_knowledge import create_factor_fuseki, create_claim_fuseki, _sparql_get_claims

    fac_a = await create_factor_fuseki(ds_id, "A", "middel", USER_ID)
    fac_b = await create_factor_fuseki(ds_id, "B", "middel", USER_ID)
    claim_id = await create_claim_fuseki(ds_id, fac_a, fac_b, "Stelling", "+", USER_ID)

    claims = await _sparql_get_claims(ds_id)
    assert len(claims) == 1
    assert claims[0]["id"] == claim_id


# ---------------------------------------------------------------------------
# DesignSpace lookup via Fuseki
# ---------------------------------------------------------------------------

async def test_get_designspace_id_for_tessera(ds_id):
    await _seed_design_space(ds_id)
    from app.db.fuseki_knowledge import create_factor_fuseki, get_designspace_id_for_tessera

    base_id = await create_factor_fuseki(ds_id, "Factor X", "middel", USER_ID)
    found_ds = await get_designspace_id_for_tessera(base_id)
    assert found_ds == ds_id


async def test_get_designspace_id_for_tessera_onbekend_geeft_none(ds_id):
    from app.db.fuseki_knowledge import get_designspace_id_for_tessera
    result = await get_designspace_id_for_tessera("niet-bestaand-id")
    assert result is None
