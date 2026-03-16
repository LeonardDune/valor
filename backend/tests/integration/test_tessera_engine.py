"""Integratietests voor app.services.fuseki_sync (Tessera-engine schrijfoperaties).

Test:
- try_write_factor: schrijft een Factor als valor:Tessera naar Fuseki
- try_write_claim: schrijft een Claim als argumentatierelatie (+/-)
- Polarity mapping: "+" → supports, "-" → undermines
"""
import pytest

from app.ontology import VALOR_NS

pytestmark = pytest.mark.integration

FACTOR_A = "factor-alpha-001"
FACTOR_B = "factor-beta-002"
CLAIM_1 = "claim-supports-001"
CLAIM_2 = "claim-undermines-002"


async def _query_graph(graph_uri: str, sparql: str) -> list[dict]:
    """Helper: voer een SPARQL SELECT uit in een specifieke named graph."""
    import httpx
    from tests.conftest import FUSEKI_TEST_URL, FUSEKI_TEST_DATASET

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


# ---------------------------------------------------------------------------
# try_write_factor
# ---------------------------------------------------------------------------

async def test_try_write_factor_maakt_tessera_aan(ds_id, user_uri):
    from app.services.fuseki_sync import try_write_factor
    from app.services.fuseki import named_graph_uri

    await try_write_factor(FACTOR_A, "Testfactor Alpha", ds_id, "user-test-001")

    graph = named_graph_uri(ds_id)
    rows = await _query_graph(graph, f"""
        SELECT ?type ?content WHERE {{
          GRAPH <{graph}> {{
            <urn:valor:tessera:{FACTOR_A}> a ?type ;
              <{VALOR_NS}claimContent> ?content .
          }}
        }}
    """)
    assert rows, "Tessera niet aangemaakt na try_write_factor"
    assert rows[0]["type"]["value"] == f"{VALOR_NS}Tessera"
    assert "Testfactor Alpha" in rows[0]["content"]["value"]


async def test_try_write_factor_zet_epistemische_status_op_proposed(ds_id):
    from app.services.fuseki_sync import try_write_factor
    from app.services.fuseki import named_graph_uri

    await try_write_factor(FACTOR_A, "Factor met status", ds_id, "user-test-001")

    graph = named_graph_uri(ds_id)
    rows = await _query_graph(graph, f"""
        SELECT ?status WHERE {{
          GRAPH <{graph}> {{
            <urn:valor:tessera:{FACTOR_A}> <{VALOR_NS}epistemicStatus> ?status .
          }}
        }}
    """)
    assert rows, "Geen epistemicStatus gevonden"
    assert "Proposed" in rows[0]["status"]["value"] or "proposed" in rows[0]["status"]["value"].lower()


async def test_try_write_factor_bevat_claimed_by(ds_id):
    from app.services.fuseki_sync import try_write_factor
    from app.services.fuseki import named_graph_uri

    await try_write_factor(FACTOR_A, "Factor met auteur", ds_id, "user-abc")

    graph = named_graph_uri(ds_id)
    rows = await _query_graph(graph, f"""
        SELECT ?user WHERE {{
          GRAPH <{graph}> {{
            <urn:valor:tessera:{FACTOR_A}> <{VALOR_NS}claimedBy> ?user .
          }}
        }}
    """)
    assert rows
    assert rows[0]["user"]["value"] == "urn:valor:user:user-abc"


async def test_try_write_factor_met_leeg_theme_id_doet_niets():
    """Lege theme_id mag geen exception gooien — stille no-op."""
    from app.services.fuseki_sync import try_write_factor

    # Geen exception verwacht
    await try_write_factor("factor-xyz", "Factor zonder theme", "", "user-001")


# ---------------------------------------------------------------------------
# try_write_claim — polarity mapping
# ---------------------------------------------------------------------------

async def test_try_write_claim_supports_schrijft_supports_relatie(ds_id):
    from app.services.fuseki_sync import try_write_factor, try_write_claim
    from app.services.fuseki import named_graph_uri

    await try_write_factor(FACTOR_A, "Alpha", ds_id, "user-001")
    await try_write_factor(FACTOR_B, "Beta", ds_id, "user-001")
    await try_write_claim(CLAIM_1, FACTOR_A, FACTOR_B, "+", ds_id)

    graph = named_graph_uri(ds_id)
    rows = await _query_graph(graph, f"""
        SELECT ?rel WHERE {{
          GRAPH <{graph}> {{
            <urn:valor:tessera:{FACTOR_A}> ?rel <urn:valor:tessera:{FACTOR_B}> .
          }}
        }}
    """)
    assert rows, "Geen relatie gevonden na try_write_claim +"
    assert "supports" in rows[0]["rel"]["value"]


async def test_try_write_claim_undermines_schrijft_undermines_relatie(ds_id):
    from app.services.fuseki_sync import try_write_factor, try_write_claim
    from app.services.fuseki import named_graph_uri

    await try_write_factor(FACTOR_A, "Alpha", ds_id, "user-001")
    await try_write_factor(FACTOR_B, "Beta", ds_id, "user-001")
    await try_write_claim(CLAIM_2, FACTOR_B, FACTOR_A, "-", ds_id)

    graph = named_graph_uri(ds_id)
    rows = await _query_graph(graph, f"""
        SELECT ?rel WHERE {{
          GRAPH <{graph}> {{
            <urn:valor:tessera:{FACTOR_B}> ?rel <urn:valor:tessera:{FACTOR_A}> .
          }}
        }}
    """)
    assert rows, "Geen relatie gevonden na try_write_claim -"
    assert "undermines" in rows[0]["rel"]["value"]


async def test_try_write_claim_met_lege_theme_id_doet_niets():
    from app.services.fuseki_sync import try_write_claim

    await try_write_claim("claim-x", "factor-a", "factor-b", "+", "")


async def test_try_write_claim_met_onbekende_polarity_schrijft_geen_relatie(ds_id):
    """Polarity anders dan '+'/'-' levert geen triple op en gooit geen exception."""
    from app.services.fuseki_sync import try_write_factor, try_write_claim
    from app.services.fuseki import named_graph_uri
    from app.services import ontology_cache

    # Tijdelijk argue_label_to_uri leegmaken om 'onbekend' te simuleren
    original = dict(ontology_cache._argue_label_to_uri)
    ontology_cache._argue_label_to_uri = {}

    try:
        await try_write_factor(FACTOR_A, "Alpha", ds_id, "user-001")
        await try_write_factor(FACTOR_B, "Beta", ds_id, "user-001")
        await try_write_claim("claim-bad", FACTOR_A, FACTOR_B, "?", ds_id)
    finally:
        ontology_cache._argue_label_to_uri = original

    graph = named_graph_uri(ds_id)
    rows = await _query_graph(graph, f"""
        SELECT ?rel WHERE {{
          GRAPH <{graph}> {{
            <urn:valor:tessera:{FACTOR_A}> ?rel <urn:valor:tessera:{FACTOR_B}> .
          }}
        }}
    """)
    assert not rows, "Er mogen geen relaties zijn bij onbekende polarity"
