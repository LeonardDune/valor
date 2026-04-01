"""Integratietests voor norm-entity functies in app.db.fuseki_entities (US-AI.7).

Test:
- create_norm_entity: URI-patroon, verplichte triples, optionele velden
- search_norms: zoeken op label en identifier, jurisdictie-filter
- get_norm_cross_perspective: cross-graph verwijzingen en lege resultaten

Gebruik:
    cd backend
    FUSEKI_URL=http://localhost:3030 pytest tests/integration/test_norm_entities.py -v
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

pytestmark = pytest.mark.integration

_ENTITIES_GRAPH = "urn:valor:entities"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _select(sparql: str) -> list[dict]:
    from app.services.fuseki import sparql_select_global
    return await sparql_select_global(sparql)


async def _ask_triple(graph: str, subject: str, predicate: str, obj: str) -> bool:
    """Geeft True als de triple aanwezig is in de opgegeven graph."""
    rows = await _select(f"""
SELECT (COUNT(*) AS ?c) WHERE {{
  GRAPH <{graph}> {{
    <{subject}> <{predicate}> <{obj}> .
  }}
}}
""")
    return int(rows[0]["c"]) > 0 if rows else False


async def _ask_literal(graph: str, subject: str, predicate: str, value: str) -> bool:
    """Geeft True als een literal-triple aanwezig is in de opgegeven graph (case-insensitive waarde-check)."""
    rows = await _select(f"""
SELECT ?val WHERE {{
  GRAPH <{graph}> {{
    <{subject}> <{predicate}> ?val .
  }}
}}
""")
    values = [r["val"].lower() if isinstance(r["val"], str) else r["val"] for r in rows]
    return value.lower() in values


# ---------------------------------------------------------------------------
# create_norm_entity — URI-patroon
# ---------------------------------------------------------------------------

async def test_create_norm_entity_geeft_slug_uri_terug():
    from app.db.fuseki_entities import create_norm_entity
    from app.ontology import VALOR_NS

    norm_type_uri = f"{VALOR_NS}lexa-ext#Law"
    uri = await create_norm_entity(norm_type_uri, "Wet op de schuldsanering", "wsnp-2024")

    assert uri == "urn:valor:entities:norm:wsnp-2024"


async def test_create_norm_entity_slug_vervangt_spaties():
    from app.db.fuseki_entities import create_norm_entity
    from app.ontology import VALOR_NS

    norm_type_uri = f"{VALOR_NS}lexa-ext#Regulation"
    uri = await create_norm_entity(norm_type_uri, "Besluit Begroting", "besluit begroting 2024")

    assert uri == "urn:valor:entities:norm:besluit-begroting-2024"


async def test_create_norm_entity_slug_vervangt_slashes():
    from app.db.fuseki_entities import create_norm_entity
    from app.ontology import VALOR_NS

    norm_type_uri = f"{VALOR_NS}lexa-ext#Law"
    uri = await create_norm_entity(norm_type_uri, "Wet Bijzondere Opnemingen", "wvggz/2020")

    assert uri == "urn:valor:entities:norm:wvggz-2020"


# ---------------------------------------------------------------------------
# create_norm_entity — verplichte triples
# ---------------------------------------------------------------------------

async def test_create_norm_entity_heeft_ufoc_normative_description_type():
    from app.db.fuseki_entities import create_norm_entity
    from app.ontology import UFOC_NS, VALOR_NS

    norm_type_uri = f"{VALOR_NS}lexa-ext#Law"
    uri = await create_norm_entity(norm_type_uri, "Wet maatschappelijke ondersteuning", "wmo-2015")

    aanwezig = await _ask_triple(
        _ENTITIES_GRAPH,
        uri,
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        f"{UFOC_NS}NormativeDescription",
    )
    assert aanwezig, "ufoc:NormativeDescription type-triple ontbreekt"


async def test_create_norm_entity_heeft_specifiek_subtype():
    from app.db.fuseki_entities import create_norm_entity
    from app.ontology import VALOR_NS

    norm_type_uri = f"{VALOR_NS}lexa-ext#Law"
    uri = await create_norm_entity(norm_type_uri, "Wet maatschappelijke ondersteuning", "wmo-2015")

    aanwezig = await _ask_triple(
        _ENTITIES_GRAPH,
        uri,
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        norm_type_uri,
    )
    assert aanwezig, "Specifiek subtype-triple ontbreekt"


async def test_create_norm_entity_heeft_beide_type_triples():
    """Norm moet zowel ufoc:NormativeDescription ALS het subtype hebben."""
    from app.db.fuseki_entities import create_norm_entity
    from app.ontology import UFOC_NS, VALOR_NS

    norm_type_uri = f"{VALOR_NS}lexa-ext#Regulation"
    uri = await create_norm_entity(norm_type_uri, "AMvB Inburgeringsbesluit", "inburgering-besluit-2021")

    rows = await _select(f"""
SELECT ?type WHERE {{
  GRAPH <{_ENTITIES_GRAPH}> {{
    <{uri}> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?type .
  }}
}}
""")
    gevonden_types = {r["type"] for r in rows}
    assert f"{UFOC_NS}NormativeDescription" in gevonden_types, "ufoc:NormativeDescription ontbreekt"
    assert norm_type_uri in gevonden_types, "Subtype ontbreekt"
    assert len(gevonden_types) == 2


# ---------------------------------------------------------------------------
# create_norm_entity — lexa:identifier en lexa:jurisdiction
# ---------------------------------------------------------------------------

async def test_create_norm_entity_slaat_lexa_identifier_op():
    from app.db.fuseki_entities import create_norm_entity
    from app.ontology import VALOR_NS

    _LEXA_NS = f"{VALOR_NS}lexa-ext#"
    norm_type_uri = f"{_LEXA_NS}Law"
    uri = await create_norm_entity(norm_type_uri, "Wet werk en bijstand", "wwb-2004")

    rows = await _select(f"""
SELECT ?id WHERE {{
  GRAPH <{_ENTITIES_GRAPH}> {{
    <{uri}> <{_LEXA_NS}identifier> ?id .
  }}
}}
""")
    assert rows, "lexa:identifier triple ontbreekt"
    assert rows[0]["id"] == "wwb-2004"


async def test_create_norm_entity_zonder_jurisdiction_slaat_niet_op():
    from app.db.fuseki_entities import create_norm_entity
    from app.ontology import VALOR_NS

    _LEXA_NS = f"{VALOR_NS}lexa-ext#"
    norm_type_uri = f"{_LEXA_NS}Law"
    uri = await create_norm_entity(norm_type_uri, "Wet zonder jurisdictie", "no-jur-001")

    rows = await _select(f"""
SELECT ?jur WHERE {{
  GRAPH <{_ENTITIES_GRAPH}> {{
    <{uri}> <{_LEXA_NS}jurisdiction> ?jur .
  }}
}}
""")
    assert rows == [], "jurisdiction moet afwezig zijn als niet opgegeven"


async def test_create_norm_entity_slaat_jurisdiction_op():
    from app.db.fuseki_entities import create_norm_entity
    from app.ontology import VALOR_NS

    _LEXA_NS = f"{VALOR_NS}lexa-ext#"
    norm_type_uri = f"{_LEXA_NS}Law"
    uri = await create_norm_entity(
        norm_type_uri,
        "Wet publieke gezondheid",
        "wpg-2008",
        jurisdiction="NL",
    )

    rows = await _select(f"""
SELECT ?jur WHERE {{
  GRAPH <{_ENTITIES_GRAPH}> {{
    <{uri}> <{_LEXA_NS}jurisdiction> ?jur .
  }}
}}
""")
    assert rows, "lexa:jurisdiction triple ontbreekt"
    assert rows[0]["jur"] == "NL"


async def test_create_norm_entity_slaat_effective_date_op():
    from app.db.fuseki_entities import create_norm_entity
    from app.ontology import VALOR_NS

    _LEXA_NS = f"{VALOR_NS}lexa-ext#"
    norm_type_uri = f"{_LEXA_NS}Law"
    uri = await create_norm_entity(
        norm_type_uri,
        "Omgevingswet",
        "ow-2024",
        effective_date="2024-01-01",
    )

    rows = await _select(f"""
SELECT ?datum WHERE {{
  GRAPH <{_ENTITIES_GRAPH}> {{
    <{uri}> <{_LEXA_NS}effectiveDate> ?datum .
  }}
}}
""")
    assert rows, "lexa:effectiveDate triple ontbreekt"
    assert "2024-01-01" in rows[0]["datum"]


# ---------------------------------------------------------------------------
# search_norms — zoeken op label
# ---------------------------------------------------------------------------

async def test_search_norms_vindt_op_label_substring():
    from app.db.fuseki_entities import create_norm_entity, search_norms
    from app.ontology import VALOR_NS

    _LEXA_NS = f"{VALOR_NS}lexa-ext#"
    await create_norm_entity(f"{_LEXA_NS}Law", "Wet op de schuldsanering", "wsnp-2024")
    await create_norm_entity(f"{_LEXA_NS}Law", "Schuldhulpverlening gemeenten", "wgs-2012")
    await create_norm_entity(f"{_LEXA_NS}Regulation", "Arbeidsomstandighedenwet", "arbo-1998")

    results = await search_norms("schuld")

    labels = [r["label"] for r in results]
    assert any("schuldsanering" in l.lower() for l in labels), "Wet op de schuldsanering niet gevonden"
    assert any("schuldhulp" in l.lower() for l in labels), "Schuldhulpverlening niet gevonden"
    assert not any("arbo" in l.lower() for l in labels), "Arbeidsomstandighedenwet mag niet in resultaten"


async def test_search_norms_is_case_insensitief():
    from app.db.fuseki_entities import create_norm_entity, search_norms
    from app.ontology import VALOR_NS

    _LEXA_NS = f"{VALOR_NS}lexa-ext#"
    await create_norm_entity(f"{_LEXA_NS}Law", "Wet Maatschappelijke Ondersteuning", "wmo-2015")

    results = await search_norms("MAATSCHAPPELIJKE")

    assert len(results) == 1
    assert "Maatschappelijke" in results[0]["label"]


# ---------------------------------------------------------------------------
# search_norms — zoeken op identifier
# ---------------------------------------------------------------------------

async def test_search_norms_vindt_op_identifier_substring():
    from app.db.fuseki_entities import create_norm_entity, search_norms
    from app.ontology import VALOR_NS

    _LEXA_NS = f"{VALOR_NS}lexa-ext#"
    await create_norm_entity(f"{_LEXA_NS}Law", "Wet bijzondere opnemingen psychiatrische ziekenhuizen", "bwbr0005537")
    await create_norm_entity(f"{_LEXA_NS}Law", "Wet langdurige zorg", "wlz-2015")

    results = await search_norms("bwbr")

    assert len(results) == 1
    assert results[0]["identifier"] == "bwbr0005537"


async def test_search_norms_leeg_resultaat_bij_geen_match():
    from app.db.fuseki_entities import create_norm_entity, search_norms
    from app.ontology import VALOR_NS

    _LEXA_NS = f"{VALOR_NS}lexa-ext#"
    await create_norm_entity(f"{_LEXA_NS}Law", "Wet werk en zekerheid", "wwz-2015")

    results = await search_norms("xyzOnbestaandeWet999")

    assert results == []


# ---------------------------------------------------------------------------
# search_norms — jurisdictie-filter
# ---------------------------------------------------------------------------

async def test_search_norms_filtert_op_jurisdictie():
    from app.db.fuseki_entities import create_norm_entity, search_norms
    from app.ontology import VALOR_NS

    _LEXA_NS = f"{VALOR_NS}lexa-ext#"
    await create_norm_entity(f"{_LEXA_NS}Law", "Wet Basisregistratie Personen", "brp-2013", jurisdiction="NL")
    await create_norm_entity(f"{_LEXA_NS}Law", "Lokale Verordening Amsterdam", "ams-2022", jurisdiction="NL-NH")
    await create_norm_entity(f"{_LEXA_NS}Law", "GDPR", "gdpr-2018", jurisdiction="EU")

    results = await search_norms("wet", jurisdiction="NL")

    assert len(results) == 1
    assert results[0]["identifier"] == "brp-2013"


async def test_search_norms_zonder_jurisdictie_filter_geeft_alles():
    from app.db.fuseki_entities import create_norm_entity, search_norms
    from app.ontology import VALOR_NS

    _LEXA_NS = f"{VALOR_NS}lexa-ext#"
    await create_norm_entity(f"{_LEXA_NS}Law", "Wet sociale werkvoorziening", "wsw-2015", jurisdiction="NL")
    await create_norm_entity(f"{_LEXA_NS}Regulation", "EU-verordening werkgelegenheid", "eu-werk-2020", jurisdiction="EU")

    results = await search_norms("we")

    assert len(results) == 2


# ---------------------------------------------------------------------------
# search_norms — teruggeef-structuur
# ---------------------------------------------------------------------------

async def test_search_norms_resultaat_bevat_verwachte_velden():
    from app.db.fuseki_entities import create_norm_entity, search_norms
    from app.ontology import VALOR_NS

    _LEXA_NS = f"{VALOR_NS}lexa-ext#"
    norm_type_uri = f"{_LEXA_NS}Law"
    await create_norm_entity(norm_type_uri, "Wet open overheid", "woo-2022", jurisdiction="NL")

    results = await search_norms("open overheid")

    assert len(results) == 1
    r = results[0]
    assert "uri" in r
    assert "norm_type_uri" in r
    assert "norm_type_local" in r
    assert "label" in r
    assert "identifier" in r
    assert "jurisdiction" in r
    assert r["norm_type_local"] == "Law"
    assert r["norm_type_uri"] == norm_type_uri


# ---------------------------------------------------------------------------
# get_norm_cross_perspective — verwijzingen in andere grafen
# ---------------------------------------------------------------------------

async def test_get_norm_cross_perspective_vindt_verwijzing_in_andere_graph():
    from app.db.fuseki_entities import create_norm_entity, get_norm_cross_perspective
    from app.services.fuseki import sparql_update
    from app.ontology import VALOR_NS

    _LEXA_NS = f"{VALOR_NS}lexa-ext#"
    norm_uri = await create_norm_entity(f"{_LEXA_NS}Law", "Wet langdurige zorg", "wlz-2015")

    # Voeg een verwijzing naar de norm-URI toe in een DesignSpace-graph
    ds_graph = "urn:valor:ds:test-cross-persp/asis"
    factor_uri = "urn:valor:tessera:factor-test-001"
    predicate = f"{VALOR_NS}regulatedBy"
    await sparql_update(f"""
INSERT DATA {{
  GRAPH <{ds_graph}> {{
    <{factor_uri}> <{predicate}> <{norm_uri}> .
  }}
}}
""", "test-cross-persp")

    results = await get_norm_cross_perspective(norm_uri)

    assert len(results) == 1
    assert results[0]["graph"] == ds_graph
    assert results[0]["subject"] == factor_uri
    assert results[0]["predicate"] == predicate


async def test_get_norm_cross_perspective_verwijzing_in_meerdere_grafen():
    from app.db.fuseki_entities import create_norm_entity, get_norm_cross_perspective
    from app.services.fuseki import sparql_update
    from app.ontology import VALOR_NS

    _LEXA_NS = f"{VALOR_NS}lexa-ext#"
    norm_uri = await create_norm_entity(f"{_LEXA_NS}Regulation", "Besluit Jeugdwet", "bjw-2015")

    predicate = f"{VALOR_NS}regulatedBy"

    for i in range(1, 4):
        graph = f"urn:valor:ds:test-ds-{i}/asis"
        subject = f"urn:valor:tessera:factor-{i}"
        await sparql_update(f"""
INSERT DATA {{
  GRAPH <{graph}> {{
    <{subject}> <{predicate}> <{norm_uri}> .
  }}
}}
""", f"test-ds-{i}")

    results = await get_norm_cross_perspective(norm_uri)

    assert len(results) == 3
    grafen = {r["graph"] for r in results}
    assert "urn:valor:ds:test-ds-1/asis" in grafen
    assert "urn:valor:ds:test-ds-2/asis" in grafen
    assert "urn:valor:ds:test-ds-3/asis" in grafen


async def test_get_norm_cross_perspective_geeft_lege_lijst_zonder_verwijzingen():
    from app.db.fuseki_entities import create_norm_entity, get_norm_cross_perspective
    from app.ontology import VALOR_NS

    _LEXA_NS = f"{VALOR_NS}lexa-ext#"
    norm_uri = await create_norm_entity(f"{_LEXA_NS}Law", "Wet zonder verwijzingen", "geen-refs-001")

    results = await get_norm_cross_perspective(norm_uri)

    assert results == []


async def test_get_norm_cross_perspective_sluit_entities_graph_uit():
    """Verwijzingen vanuit urn:valor:entities zelf mogen niet in het resultaat."""
    from app.db.fuseki_entities import create_norm_entity, get_norm_cross_perspective
    from app.services.fuseki import sparql_update
    from app.ontology import VALOR_NS, UFOC_NS

    _LEXA_NS = f"{VALOR_NS}lexa-ext#"
    norm_uri = await create_norm_entity(f"{_LEXA_NS}Law", "Wet zorg en dwang", "wzd-2020")

    # Voeg een triple toe die naar de norm verwijst, MAAR in de entities-graph zelf
    # Dit simuleert bijv. een relatie tussen twee normen in hetzelfde register
    other_norm_uri = await create_norm_entity(f"{_LEXA_NS}Law", "Aanverwante wet", "aanverwant-001")
    await sparql_update(f"""
INSERT DATA {{
  GRAPH <{_ENTITIES_GRAPH}> {{
    <{other_norm_uri}> <{_LEXA_NS}relatedNorm> <{norm_uri}> .
  }}
}}
""", "entities")

    results = await get_norm_cross_perspective(norm_uri)

    # entities-graph is uitgesloten — resultaat moet leeg zijn
    assert results == []


async def test_get_norm_cross_perspective_resultaat_bevat_predicate_local():
    from app.db.fuseki_entities import create_norm_entity, get_norm_cross_perspective
    from app.services.fuseki import sparql_update
    from app.ontology import VALOR_NS

    _LEXA_NS = f"{VALOR_NS}lexa-ext#"
    norm_uri = await create_norm_entity(f"{_LEXA_NS}Law", "Wet inburgering", "wi-2021")

    predicate = f"{VALOR_NS}regulatedBy"
    await sparql_update(f"""
INSERT DATA {{
  GRAPH <urn:valor:ds:test-local/asis> {{
    <urn:valor:tessera:factor-local> <{predicate}> <{norm_uri}> .
  }}
}}
""", "test-local")

    results = await get_norm_cross_perspective(norm_uri)

    assert len(results) == 1
    assert results[0]["predicate_local"] == "regulatedBy"
