"""Integratietests voor app.services.fuseki.

Test de kernfuncties van de Fuseki-servicelaag:
- initialize_design_space_graphs
- initialize_alternative_graph
- sparql_select / sparql_select_global
- sparql_update
- sparql_proxy_query (isolatie + read-only handhaving)
"""
import pytest


pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# initialize_design_space_graphs
# ---------------------------------------------------------------------------

async def test_initialize_design_space_graphs_maakt_vijf_named_graphs(ds_id):
    from app.services.fuseki import initialize_design_space_graphs, sparql_select_global

    issue_uri = f"urn:valor:issue:{ds_id}"
    named_graphs = await initialize_design_space_graphs(ds_id, issue_uri)

    assert set(named_graphs.keys()) == {"base", "asis", "decisions", "agents", "provenance"}

    existing = await sparql_select_global(
        "SELECT DISTINCT ?g WHERE { GRAPH ?g { } }"
    )
    existing_uris = {row["g"] for row in existing}
    for g in named_graphs.values():
        assert g in existing_uris, f"Named graph ontbreekt: {g}"


async def test_initialize_design_space_graphs_schrijft_metadata_in_base(ds_id):
    from app.services.fuseki import initialize_design_space_graphs, sparql_select_global
    from app.ontology import VALOR_NS

    issue_uri = f"urn:valor:issue:{ds_id}"
    graphs = await initialize_design_space_graphs(ds_id, issue_uri)
    base = graphs["base"]

    rows = await sparql_select_global(
        f"SELECT ?p ?o WHERE {{ GRAPH <{base}> {{ <urn:valor:ds:{ds_id}> ?p ?o }} }}"
    )
    predicates = {row["p"] for row in rows}

    assert f"{VALOR_NS}isAddressedInDesignSpace" in predicates
    assert f"{VALOR_NS}hasGraph" in predicates


async def test_initialize_design_space_graphs_is_idempotent(ds_id):
    """Twee keer aanroepen mag niet crashen (INSERT DATA is niet MERGE, maar wel tolerant)."""
    from app.services.fuseki import initialize_design_space_graphs

    issue_uri = f"urn:valor:issue:{ds_id}"
    await initialize_design_space_graphs(ds_id, issue_uri)
    # Tweede aanroep mag geen exception gooien
    await initialize_design_space_graphs(ds_id, issue_uri)


# ---------------------------------------------------------------------------
# initialize_alternative_graph
# ---------------------------------------------------------------------------

async def test_initialize_alternative_graph_schrijft_metadata(ds_id, user_uri):
    from app.services.fuseki import (
        initialize_design_space_graphs,
        initialize_alternative_graph,
        sparql_select_global,
    )
    from app.ontology import VALOR_NS

    issue_uri = f"urn:valor:issue:{ds_id}"
    await initialize_design_space_graphs(ds_id, issue_uri)

    alt_id = "alt-001"
    alt_uri = await initialize_alternative_graph(
        ds_id=ds_id,
        alt_id=alt_id,
        name="Alternatief A",
        description="Eerste alternatief",
        creator_uri=user_uri,
        created_at="2026-03-16T00:00:00+00:00",
    )

    assert alt_uri == f"urn:valor:ds:{ds_id}/alternative/{alt_id}"

    base_graph = f"urn:valor:ds:{ds_id}/base"
    rows = await sparql_select_global(
        f"SELECT ?p ?o WHERE {{ GRAPH <{base_graph}> {{ <{alt_uri}> ?p ?o }} }}"
    )
    predicates = {row["p"] for row in rows}
    assert f"{VALOR_NS}alternativeName" in predicates
    assert f"{VALOR_NS}createdBy" in predicates


# ---------------------------------------------------------------------------
# sparql_proxy_query — isolatie en read-only
# ---------------------------------------------------------------------------

async def test_sparql_proxy_query_weigert_update(ds_id):
    from app.services.fuseki import initialize_design_space_graphs, sparql_proxy_query
    from fastapi import HTTPException

    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")

    with pytest.raises(HTTPException) as exc_info:
        await sparql_proxy_query(
            "INSERT DATA { <urn:test:s> <urn:test:p> <urn:test:o> }",
            ds_id,
        )
    assert exc_info.value.status_code == 400


async def test_sparql_proxy_query_weigert_delete(ds_id):
    from app.services.fuseki import initialize_design_space_graphs, sparql_proxy_query
    from fastapi import HTTPException

    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")

    with pytest.raises(HTTPException):
        await sparql_proxy_query("DELETE WHERE { ?s ?p ?o }", ds_id)


async def test_sparql_proxy_query_retourneert_resultaten_binnen_scope(ds_id):
    from app.services.fuseki import initialize_design_space_graphs, sparql_proxy_query

    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")

    result = await sparql_proxy_query("SELECT ?s ?p ?o WHERE { ?s ?p ?o }", ds_id)
    assert "results" in result
    bindings = result["results"]["bindings"]
    assert len(bindings) > 0  # base-graph heeft marker-triples


async def test_sparql_proxy_query_ziet_geen_andere_designspace_data(ds_id):
    """Data van een andere DesignSpace mag niet zichtbaar zijn via de proxy."""
    from app.services.fuseki import (
        initialize_design_space_graphs,
        sparql_update,
        sparql_proxy_query,
    )
    from app.ontology import VALOR_NS

    other_ds = "andere-ds-buiten-scope"
    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{ds_id}")
    await initialize_design_space_graphs(other_ds, f"urn:valor:issue:{other_ds}")

    # Schrijf een unieke triple in de andere DesignSpace
    other_asis = f"urn:valor:ds:{other_ds}/asis"
    geheim_subject = "urn:valor:geheim:triple"
    await sparql_update(
        f"INSERT DATA {{ GRAPH <{other_asis}> {{ <{geheim_subject}> <urn:test:p> <urn:test:o> }} }}",
        other_ds,
    )

    # Query via de proxy van ds_id — mag het geheime subject NIET zien
    result = await sparql_proxy_query(
        f"ASK {{ <{geheim_subject}> ?p ?o }}", ds_id
    )
    assert result.get("boolean") is False
