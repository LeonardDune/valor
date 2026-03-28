"""Integratietests voor de SPARQL-proxy (isolatie en toegangscontrole).

Test:
- Alleen SELECT/CONSTRUCT/ASK/DESCRIBE worden geaccepteerd
- Data van andere DesignSpaces is niet zichtbaar
- CONSTRUCT retourneert Turtle
- ASK retourneert een boolean
"""
import pytest

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Read-only handhaving
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("query", [
    "INSERT DATA { <urn:s> <urn:p> <urn:o> }",
    "DELETE WHERE { ?s ?p ?o }",
    "INSERT { ?s ?p ?o } WHERE { ?s ?p ?o }",
    "CLEAR GRAPH <urn:valor:ds:test/asis>",
    "DROP GRAPH <urn:valor:ds:test/asis>",
    "LOAD <http://example.org/data>",
])
async def test_proxy_weigert_schrijfoperaties(ds_id, query):
    from app.services.fuseki import initialize_design_space_graphs, sparql_proxy_query
    from fastapi import HTTPException

    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")

    with pytest.raises(HTTPException) as exc_info:
        await sparql_proxy_query(query, ds_id)
    assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# SELECT binnen scope
# ---------------------------------------------------------------------------

async def test_proxy_select_retourneert_resultaten(ds_id):
    from app.services.fuseki import initialize_design_space_graphs, sparql_proxy_query

    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")

    result = await sparql_proxy_query("SELECT ?s ?p ?o WHERE { ?s ?p ?o }", ds_id)
    assert "results" in result
    assert "bindings" in result["results"]
    assert len(result["results"]["bindings"]) > 0


# ---------------------------------------------------------------------------
# ASK
# ---------------------------------------------------------------------------

async def test_proxy_ask_retourneert_boolean(ds_id):
    from app.services.fuseki import initialize_design_space_graphs, sparql_proxy_query

    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")

    result = await sparql_proxy_query("ASK { ?s ?p ?o }", ds_id)
    assert "boolean" in result
    assert result["boolean"] is True


async def test_proxy_ask_retourneert_false_voor_onbekend_subject(ds_id):
    from app.services.fuseki import initialize_design_space_graphs, sparql_proxy_query

    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")

    result = await sparql_proxy_query(
        "ASK { <urn:valor:bestaat:niet> ?p ?o }", ds_id
    )
    assert result["boolean"] is False


# ---------------------------------------------------------------------------
# Graph-isolatie tussen twee DesignSpaces
# ---------------------------------------------------------------------------

async def test_proxy_ziet_geen_data_van_andere_designspace(ds_id):
    from app.services.fuseki import (
        initialize_design_space_graphs,
        sparql_update,
        sparql_proxy_query,
    )

    ds_other = "ds-extern-123"
    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")
    await initialize_design_space_graphs(ds_other, f"urn:valor:issue:{ds_other}")

    # Schrijf een uniek subject in de as-is graph van de andere DesignSpace
    extern_subject = "urn:valor:extern:geheim"
    await sparql_update(
        f"INSERT DATA {{ GRAPH <urn:valor:ds:{ds_other}/asis> {{ "
        f"<{extern_subject}> <urn:test:p> <urn:test:o> }} }}",
        ds_other,
    )

    result = await sparql_proxy_query(
        f"ASK {{ <{extern_subject}> ?p ?o }}", ds_id
    )
    assert result["boolean"] is False, (
        "Proxy laat data van een andere DesignSpace zien — isolatie werkt niet"
    )


async def test_proxy_ziet_eigen_data_wel(ds_id, user_uri):
    from app.services.fuseki import (
        initialize_design_space_graphs,
        sparql_update,
        sparql_proxy_query,
    )

    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")

    eigen_subject = "urn:valor:eigen:triple"
    await sparql_update(
        f"INSERT DATA {{ GRAPH <urn:valor:ds:{ds_id}/baseline> {{ "
        f"<{eigen_subject}> <urn:test:p> <urn:test:o> }} }}",
        ds_id,
    )

    result = await sparql_proxy_query(
        f"ASK {{ <{eigen_subject}> ?p ?o }}", ds_id
    )
    assert result["boolean"] is True
