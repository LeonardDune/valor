"""Integratietests voor POST /tessera/{id}/realise en causa:realisedBy (US-4.6).

Test de SPARQL-schrijfoperaties voor het koppelen van een Intervention aan
een acta:TransactionType via causa:realisedBy.

Gebruik:
    cd backend
    FUSEKI_URL=http://localhost:3030 pytest tests/integration/test_tessera_realise.py -v
"""
import sys
import os
import uuid

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.ontology import VALOR_NS
from app.services.fuseki import (
    initialize_design_space_graphs,
    initialize_alternative_graph,
    sparql_select_global,
    sparql_update,
)

pytestmark = pytest.mark.integration

USER_ID = "user-realise-test-001"
USER_URI = f"urn:valor:user:{USER_ID}"
CAUSA_REALISED_BY = f"{VALOR_NS}causa#realisedBy"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_tessera_in_alternative(ds_id: str, alt_id: str, user_uri: str) -> str:
    """Maakt een Tessera aan in de alternatief-graph en retourneert de tessera_id."""
    tessera_id = str(uuid.uuid4())
    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    graph_uri = f"urn:valor:ds:{ds_id}/alternative/{alt_id}"
    proposed_uri = f"{VALOR_NS}ProposedStatus"

    await sparql_update(
        f"""INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> a <{VALOR_NS}Tessera> ;
      <{VALOR_NS}claimContent> "Test Tessera"@nl ;
      <{VALOR_NS}epistemicStatus> <{proposed_uri}> ;
      <{VALOR_NS}claimedBy> <{user_uri}> ;
      <{VALOR_NS}claimedAt> "2026-03-21T00:00:00Z"^^<http://www.w3.org/2001/XMLSchema#dateTime> .
  }}
}}""",
        ds_id,
    )
    return tessera_id


async def _get_realised_by(ds_id: str, alt_id: str, tessera_uri: str) -> str | None:
    """Leest de causa:realisedBy waarde van een Tessera uit de alternatief-graph."""
    graph_uri = f"urn:valor:ds:{ds_id}/alternative/{alt_id}"
    rows = await sparql_select_global(
        f"""SELECT ?tx WHERE {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> <{CAUSA_REALISED_BY}> ?tx .
  }}
}}"""
    )
    return rows[0]["tx"] if rows else None


# ---------------------------------------------------------------------------
# Tests: causa:realisedBy schrijven
# ---------------------------------------------------------------------------

async def test_realise_slaat_triple_op_in_alternatief_graph(ds_id):
    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")
    alt_id = "alt-realise-001"
    await initialize_alternative_graph(
        ds_id, alt_id, "Test Alternatief", "Beschrijving", USER_URI, "2026-03-21T00:00:00Z"
    )

    tessera_id = await _create_tessera_in_alternative(ds_id, alt_id, USER_URI)
    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    tx_uri = "urn:acta:transactiontype:subsidie-verstrekking"
    graph_uri = f"urn:valor:ds:{ds_id}/alternative/{alt_id}"

    # Direct schrijven via SPARQL (test de laag zonder HTTP)
    await sparql_update(
        f"""INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> <{CAUSA_REALISED_BY}> <{tx_uri}> .
  }}
}}""",
        ds_id,
    )

    result = await _get_realised_by(ds_id, alt_id, tessera_uri)
    assert result == tx_uri


async def test_realise_is_idempotent_bij_herschrijven(ds_id):
    """Herschrijven van causa:realisedBy vervangt de bestaande waarde."""
    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")
    alt_id = "alt-realise-002"
    await initialize_alternative_graph(
        ds_id, alt_id, "Test Alternatief", "", USER_URI, "2026-03-21T00:00:00Z"
    )

    tessera_id = await _create_tessera_in_alternative(ds_id, alt_id, USER_URI)
    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    graph_uri = f"urn:valor:ds:{ds_id}/alternative/{alt_id}"
    tx_uri_1 = "urn:acta:transactiontype:eerste-type"
    tx_uri_2 = "urn:acta:transactiontype:tweede-type"

    await sparql_update(
        f"""INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> <{CAUSA_REALISED_BY}> <{tx_uri_1}> .
  }}
}}""",
        ds_id,
    )

    # Idempotent: verwijder en herschrijf
    await sparql_update(
        f"""DELETE WHERE {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> <{CAUSA_REALISED_BY}> ?any .
  }}
}}""",
        ds_id,
    )
    await sparql_update(
        f"""INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> <{CAUSA_REALISED_BY}> <{tx_uri_2}> .
  }}
}}""",
        ds_id,
    )

    result = await _get_realised_by(ds_id, alt_id, tessera_uri)
    assert result == tx_uri_2

    # Controleer geen dubbele triples
    graph_uri_safe = f"urn:valor:ds:{ds_id}/alternative/{alt_id}"
    rows = await sparql_select_global(
        f"""SELECT ?tx WHERE {{
  GRAPH <{graph_uri_safe}> {{
    <{tessera_uri}> <{CAUSA_REALISED_BY}> ?tx .
  }}
}}"""
    )
    assert len(rows) == 1


async def test_realise_detectie_ontbrekende_realisatiebasis(ds_id):
    """SPARQL-query detecteert Interventions zonder geldige TransactionType in het alternatief."""
    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")
    alt_id = "alt-realise-003"
    await initialize_alternative_graph(
        ds_id, alt_id, "Test Alternatief", "", USER_URI, "2026-03-21T00:00:00Z"
    )

    tessera_id = await _create_tessera_in_alternative(ds_id, alt_id, USER_URI)
    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    graph_uri = f"urn:valor:ds:{ds_id}/alternative/{alt_id}"
    # tx_uri is NIET geregistreerd als includesTransaction → ontbrekende basis
    tx_uri = "urn:acta:transactiontype:niet-geregistreerd"

    await sparql_update(
        f"""INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> <{CAUSA_REALISED_BY}> <{tx_uri}> .
  }}
}}""",
        ds_id,
    )

    includes_tx = f"{VALOR_NS}includesTransaction"
    rows = await sparql_select_global(
        f"""SELECT ?intervention ?tx ?alt WHERE {{
  GRAPH ?alt {{
    ?intervention <{CAUSA_REALISED_BY}> ?tx .
    FILTER(STRSTARTS(STR(?alt), "urn:valor:ds:{ds_id}/alternative/"))
    FILTER NOT EXISTS {{
      ?alt <{includes_tx}> ?tx .
    }}
  }}
}}"""
    )

    assert len(rows) == 1
    assert rows[0]["intervention"] == tessera_uri
    assert rows[0]["tx"] == tx_uri


async def test_realise_geen_detectie_als_transactiontype_aanwezig(ds_id):
    """Geen ontbrekende basis als TransactionType wel geregistreerd is."""
    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")
    alt_id = "alt-realise-004"
    await initialize_alternative_graph(
        ds_id, alt_id, "Test Alternatief", "", USER_URI, "2026-03-21T00:00:00Z"
    )

    tessera_id = await _create_tessera_in_alternative(ds_id, alt_id, USER_URI)
    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    graph_uri = f"urn:valor:ds:{ds_id}/alternative/{alt_id}"
    tx_uri = "urn:acta:transactiontype:geregistreerd"
    includes_tx = f"{VALOR_NS}includesTransaction"
    alt_uri = f"urn:valor:ds:{ds_id}/alternative/{alt_id}"

    await sparql_update(
        f"""INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> <{CAUSA_REALISED_BY}> <{tx_uri}> .
    <{alt_uri}> <{includes_tx}> <{tx_uri}> .
  }}
}}""",
        ds_id,
    )

    rows = await sparql_select_global(
        f"""SELECT ?intervention ?tx ?alt WHERE {{
  GRAPH ?alt {{
    ?intervention <{CAUSA_REALISED_BY}> ?tx .
    FILTER(STRSTARTS(STR(?alt), "urn:valor:ds:{ds_id}/alternative/"))
    FILTER NOT EXISTS {{
      ?alt <{includes_tx}> ?tx .
    }}
  }}
}}"""
    )

    assert len(rows) == 0
