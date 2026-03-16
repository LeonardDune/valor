"""Integratietests voor de disc:ContributionType ontologie (US-16.1).

Verifieert:
- Na het laden van disc-triples in Fuseki retourneert een SPARQL-query
  de zes disc:ContributionType instanties.
- load_ontology_cache() vult _disc_contribution_type_label_to_uri correct.
"""
import pytest

pytestmark = pytest.mark.integration

DISC_NS = "https://valor-ecosystem.nl/ontology/disc#"
DISC_GRAPH = "https://valor-ecosystem.nl/ontology/disc"

EXPECTED_CONTRIBUTION_TYPES = {
    "Vraag",
    "Stelling",
    "Bewijs",
    "Bezwaar",
    "Toelichting",
    "Akkoord",
}

_DISC_SEED_UPDATE = f"""
PREFIX disc:  <{DISC_NS}>
PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:   <http://www.w3.org/2002/07/owl#>
PREFIX prov:  <https://www.w3.org/ns/prov#>

INSERT DATA {{
  GRAPH <{DISC_GRAPH}> {{
    disc:ContributionType a owl:Class .

    disc:Vraag       a disc:ContributionType ; rdfs:label "Vraag"@nl .
    disc:Stelling    a disc:ContributionType ; rdfs:label "Stelling"@nl .
    disc:Bewijs      a disc:ContributionType ; rdfs:label "Bewijs"@nl .
    disc:Bezwaar     a disc:ContributionType ; rdfs:label "Bezwaar"@nl .
    disc:Toelichting a disc:ContributionType ; rdfs:label "Toelichting"@nl .
    disc:Akkoord     a disc:ContributionType ; rdfs:label "Akkoord"@nl .

    disc:DiscussionThread  a owl:Class ; rdfs:subClassOf prov:Activity .
    disc:ThreadContribution a owl:Class ; rdfs:subClassOf prov:Activity .
    disc:ThreadResolution  a owl:Class ; rdfs:subClassOf prov:Entity .
  }}
}}
"""


@pytest.fixture
async def disc_graph_seeded():
    """Seed de disc-module triples in de test-Fuseki instantie."""
    from app.services.fuseki import sparql_select_global
    import app.services.fuseki as fs
    import httpx

    url = f"{fs.FUSEKI_URL}/{fs.FUSEKI_DATASET}/update"
    async with httpx.AsyncClient() as client:
        r = await client.post(
            url,
            data={"update": _DISC_SEED_UPDATE},
            auth=("admin", fs.FUSEKI_ADMIN_PASSWORD),
            timeout=15,
        )
        r.raise_for_status()


# ---------------------------------------------------------------------------
# SPARQL-query test
# ---------------------------------------------------------------------------

async def test_sparql_retourneert_zes_contribution_types(disc_graph_seeded):
    from app.services.fuseki import sparql_select_global

    rows = await sparql_select_global(f"""
        PREFIX disc: <{DISC_NS}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?uri ?label WHERE {{
          GRAPH <{DISC_GRAPH}> {{
            ?uri a disc:ContributionType ;
                 rdfs:label ?label .
            FILTER(lang(?label) = "nl")
          }}
        }}
    """)

    labels = {row["label"] for row in rows}
    assert labels == EXPECTED_CONTRIBUTION_TYPES, (
        f"Verwachte types: {EXPECTED_CONTRIBUTION_TYPES}, gevonden: {labels}"
    )


async def test_sparql_retourneert_drie_disc_klassen(disc_graph_seeded):
    from app.services.fuseki import sparql_select_global

    rows = await sparql_select_global(f"""
        PREFIX disc: <{DISC_NS}>
        PREFIX owl:  <http://www.w3.org/2002/07/owl#>
        SELECT ?uri WHERE {{
          GRAPH <{DISC_GRAPH}> {{
            ?uri a owl:Class .
          }}
        }}
    """)

    uris = {row["uri"] for row in rows}
    assert f"{DISC_NS}DiscussionThread" in uris
    assert f"{DISC_NS}ThreadContribution" in uris
    assert f"{DISC_NS}ThreadResolution" in uris
    assert f"{DISC_NS}ContributionType" in uris


# ---------------------------------------------------------------------------
# Ontologie-cache test
# ---------------------------------------------------------------------------

async def test_load_ontology_cache_vult_disc_contribution_types(disc_graph_seeded):
    from app.services.ontology_cache import (
        load_ontology_cache,
        get_disc_contribution_type_label_to_uri,
    )

    await load_ontology_cache()

    disc_types = get_disc_contribution_type_label_to_uri()
    assert set(disc_types.keys()) == EXPECTED_CONTRIBUTION_TYPES

    for label, uri in disc_types.items():
        assert uri.startswith(DISC_NS), f"URI {uri} heeft niet de verwachte disc namespace"
        assert uri == f"{DISC_NS}{label}", f"URI voor '{label}' klopt niet: {uri}"
