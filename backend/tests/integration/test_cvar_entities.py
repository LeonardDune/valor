"""Integratietests voor CausalVariable-functies in app.db.fuseki_entities (US-AI.8).

Test:
- create_causal_variable: URI-patroon, verplichte en optionele triples
- search_cvars: zoeken op label, optionele domein-filter
- get_cvar: ophalen op URI, niet-bestaande URI

Gebruik:
    cd backend
    FUSEKI_URL=http://localhost:3030 pytest tests/integration/test_cvar_entities.py -v
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

pytestmark = pytest.mark.integration

_ENTITIES_GRAPH = "urn:valor:entities"
_CAUSA_NS = "https://valor-ecosystem.nl/ontology/causa#"
_VALOR_NS = "https://valor-ecosystem.nl/ontology/"
_RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
_RDFS_COMMENT = "http://www.w3.org/2000/01/rdf-schema#comment"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _select(sparql: str) -> list[dict]:
    from app.services.fuseki import sparql_select_global
    return await sparql_select_global(sparql)


async def _ask_triple(graph: str, subject: str, predicate: str, obj: str) -> bool:
    rows = await _select(f"""
SELECT (COUNT(*) AS ?c) WHERE {{
  GRAPH <{graph}> {{
    <{subject}> <{predicate}> <{obj}> .
  }}
}}
""")
    return int(rows[0]["c"]) > 0 if rows else False


async def _ask_literal(graph: str, subject: str, predicate: str, value: str) -> bool:
    rows = await _select(f"""
SELECT ?val WHERE {{
  GRAPH <{graph}> {{
    <{subject}> <{predicate}> ?val .
  }}
}}
""")
    return any(value.lower() in str(r.get("val", "")).lower() for r in rows)


async def _delete_cvar(uri: str) -> None:
    from app.services.fuseki import sparql_update
    await sparql_update(
        f"DELETE WHERE {{ GRAPH <{_ENTITIES_GRAPH}> {{ <{uri}> ?p ?o }} }}",
        "entities",
    )


# ---------------------------------------------------------------------------
# create_causal_variable
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_cvar_geeft_urn_uri_terug():
    from app.db.fuseki_entities import create_causal_variable
    uri = await create_causal_variable(label="Test Variabele", identifier="test-var-uri")
    try:
        assert uri == f"{_ENTITIES_GRAPH}:cvar:test-var-uri"
    finally:
        await _delete_cvar(uri)


@pytest.mark.asyncio
async def test_create_cvar_schrijft_rdf_type():
    from app.db.fuseki_entities import create_causal_variable
    uri = await create_causal_variable(label="Recidivecijfer", identifier="recidivecijfer")
    try:
        has_type = await _ask_triple(
            _ENTITIES_GRAPH, uri,
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
            f"{_CAUSA_NS}CausalVariable",
        )
        assert has_type, "rdf:type causa:CausalVariable ontbreekt"
    finally:
        await _delete_cvar(uri)


@pytest.mark.asyncio
async def test_create_cvar_schrijft_label():
    from app.db.fuseki_entities import create_causal_variable
    uri = await create_causal_variable(label="Wachttijd jeugdzorg", identifier="wachttijd-jeugdzorg")
    try:
        has_label = await _ask_literal(_ENTITIES_GRAPH, uri, _RDFS_LABEL, "wachttijd jeugdzorg")
        assert has_label, "rdfs:label ontbreekt"
    finally:
        await _delete_cvar(uri)


@pytest.mark.asyncio
async def test_create_cvar_schrijft_optioneel_domain():
    from app.db.fuseki_entities import create_causal_variable
    uri = await create_causal_variable(
        label="Zorgkosten",
        identifier="zorgkosten-test",
        domain="gezondheidszorg",
    )
    try:
        has_domain = await _ask_literal(
            _ENTITIES_GRAPH, uri, f"{_VALOR_NS}domain", "gezondheidszorg"
        )
        assert has_domain, "valor:domain ontbreekt"
    finally:
        await _delete_cvar(uri)


@pytest.mark.asyncio
async def test_create_cvar_schrijft_optioneel_unit():
    from app.db.fuseki_entities import create_causal_variable
    uri = await create_causal_variable(
        label="Gemiddeld Inkomen",
        identifier="gemiddeld-inkomen-test",
        unit="EUR/jaar",
    )
    try:
        has_unit = await _ask_literal(
            _ENTITIES_GRAPH, uri, f"{_VALOR_NS}unit", "EUR/jaar"
        )
        assert has_unit, "valor:unit ontbreekt"
    finally:
        await _delete_cvar(uri)


@pytest.mark.asyncio
async def test_create_cvar_schrijft_optioneel_comment():
    from app.db.fuseki_entities import create_causal_variable
    uri = await create_causal_variable(
        label="Schuldendruk",
        identifier="schuldendruk-test",
        comment="Gemiddelde schuldenlast als % van inkomen",
    )
    try:
        has_comment = await _ask_literal(
            _ENTITIES_GRAPH, uri, _RDFS_COMMENT, "schuldenlast"
        )
        assert has_comment, "rdfs:comment ontbreekt"
    finally:
        await _delete_cvar(uri)


@pytest.mark.asyncio
async def test_create_cvar_zonder_identifier_genereert_uuid():
    from app.db.fuseki_entities import create_causal_variable
    uri = await create_causal_variable(label="Armoederisico")
    try:
        assert uri.startswith(f"{_ENTITIES_GRAPH}:cvar:")
        slug = uri.split(":cvar:")[-1]
        # UUID heeft 32 hex-chars + 4 streepjes = 36 tekens
        assert len(slug) == 36, f"Verwacht UUID-slug maar kreeg: {slug}"
    finally:
        await _delete_cvar(uri)


@pytest.mark.asyncio
async def test_create_cvar_schrijft_entity_id():
    from app.db.fuseki_entities import create_causal_variable
    uri = await create_causal_variable(label="Criminaliteitscijfer", identifier="criminaliteit-test")
    try:
        has_id = await _ask_literal(
            _ENTITIES_GRAPH, uri, f"{_VALOR_NS}entityId", "criminaliteit-test"
        )
        assert has_id, "valor:entityId ontbreekt"
    finally:
        await _delete_cvar(uri)


# ---------------------------------------------------------------------------
# search_cvars
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_cvars_vindt_op_label():
    from app.db.fuseki_entities import create_causal_variable, search_cvars
    uri = await create_causal_variable(label="Werkloosheidscijfer NL", identifier="werkloosheid-nl-search")
    try:
        results = await search_cvars("werkloosheid")
        uris = [r["uri"] for r in results]
        assert uri in uris, f"Verwachtte {uri} in zoekresultaten"
    finally:
        await _delete_cvar(uri)


@pytest.mark.asyncio
async def test_search_cvars_case_insensitief():
    from app.db.fuseki_entities import create_causal_variable, search_cvars
    uri = await create_causal_variable(label="Energieprijzen", identifier="energieprijzen-case-test")
    try:
        results = await search_cvars("ENERGIEPRIJZEN")
        uris = [r["uri"] for r in results]
        assert uri in uris
    finally:
        await _delete_cvar(uri)


@pytest.mark.asyncio
async def test_search_cvars_filtert_op_domain():
    from app.db.fuseki_entities import create_causal_variable, search_cvars
    uri_a = await create_causal_variable(
        label="Luchtkwaliteit", identifier="luchtkwaliteit-dom-test",
        domain="milieu"
    )
    uri_b = await create_causal_variable(
        label="Zorgwachttijd", identifier="zorgwachttijd-dom-test",
        domain="gezondheidszorg"
    )
    try:
        results = await search_cvars("a", domain="milieu")
        uris = [r["uri"] for r in results]
        assert uri_a in uris, "milieu-variabele niet gevonden"
        assert uri_b not in uris, "gezondheidszorg-variabele mag niet in milieu-resultaten"
    finally:
        await _delete_cvar(uri_a)
        await _delete_cvar(uri_b)


@pytest.mark.asyncio
async def test_search_cvars_retourneert_entity_type_causalvariable():
    from app.db.fuseki_entities import create_causal_variable, search_cvars
    uri = await create_causal_variable(label="Participatiegraad", identifier="participatie-type-test")
    try:
        results = await search_cvars("participatiegraad")
        match = next((r for r in results if r["uri"] == uri), None)
        assert match is not None
        assert match["entity_type"] == "CausalVariable"
    finally:
        await _delete_cvar(uri)


@pytest.mark.asyncio
async def test_search_cvars_geeft_lege_lijst_bij_geen_match():
    from app.db.fuseki_entities import search_cvars
    results = await search_cvars("xyznonexistentcvar12345")
    assert results == []


# ---------------------------------------------------------------------------
# get_cvar
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_cvar_retourneert_volledige_data():
    from app.db.fuseki_entities import create_causal_variable, get_cvar
    uri = await create_causal_variable(
        label="Belastingdruk",
        identifier="belastingdruk-get-test",
        domain="economie",
        unit="%",
        comment="Totale belastingdruk als percentage van BBP",
    )
    try:
        result = await get_cvar(uri)
        assert result is not None
        assert result["uri"] == uri
        assert result["entity_type"] == "CausalVariable"
        assert "belastingdruk" in result["label"].lower()
        assert result["domain"] == "economie"
        assert result["unit"] == "%"
        assert result["entity_id"] == "belastingdruk-get-test"
    finally:
        await _delete_cvar(uri)


@pytest.mark.asyncio
async def test_get_cvar_geeft_none_voor_niet_bestaande_uri():
    from app.db.fuseki_entities import get_cvar
    result = await get_cvar("urn:valor:entities:cvar:bestaat-niet-xyz")
    assert result is None


@pytest.mark.asyncio
async def test_get_cvar_geeft_none_voor_andere_entity_type():
    """Een PhysicalAgent mag niet als CausalVariable worden opgehaald."""
    from app.db.fuseki_entities import create_entity, get_cvar
    uri = await create_entity("PhysicalAgent", "Test Persoon", identifier="test-persoon-cvar-guard")
    try:
        result = await get_cvar(uri)
        assert result is None, "get_cvar mag geen PhysicalAgent teruggeven"
    finally:
        from app.services.fuseki import sparql_update
        await sparql_update(
            f"DELETE WHERE {{ GRAPH <{_ENTITIES_GRAPH}> {{ <{uri}> ?p ?o }} }}",
            "entities",
        )


# ---------------------------------------------------------------------------
# Hergebruik: zelfde slug = zelfde URI (idempotentie via slug)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_cvar_slug_is_deterministisch():
    """Dezelfde identifier geeft altijd dezelfde URI (hergebruik-principe)."""
    from app.db.fuseki_entities import create_causal_variable
    uri1 = await create_causal_variable(label="Ongelijkheid", identifier="ongelijkheid-idem")
    uri2 = await create_causal_variable(label="Ongelijkheid V2", identifier="ongelijkheid-idem")
    try:
        assert uri1 == uri2, "Dezelfde identifier moet dezelfde URI opleveren"
    finally:
        await _delete_cvar(uri1)
