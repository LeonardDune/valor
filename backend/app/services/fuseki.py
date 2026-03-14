import os
import logging
from typing import Any

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

FUSEKI_URL = os.getenv("FUSEKI_URL", "http://fuseki:3030")
FUSEKI_DATASET = "valor"
FUSEKI_ADMIN_PASSWORD = os.getenv("FUSEKI_ADMIN_PASSWORD", "admin")

_SPARQL_ENDPOINT = f"{FUSEKI_URL}/{FUSEKI_DATASET}/sparql"
_UPDATE_ENDPOINT = f"{FUSEKI_URL}/{FUSEKI_DATASET}/update"


def named_graph_uri(named_graph: str) -> str:
    """Geeft de volledige named graph URI voor een DesignSpace identifier."""
    return f"urn:valor:ds:{named_graph}"


def _raise_for_fuseki_error(response: httpx.Response) -> None:
    if response.status_code >= 400:
        logger.error(
            "Fuseki fout %s: %s", response.status_code, response.text[:500]
        )
        raise HTTPException(
            status_code=502,
            detail=f"Fuseki fout ({response.status_code}): {response.text[:200]}",
        )


async def sparql_select(query: str, named_graph: str) -> list[dict[str, Any]]:
    """Voert een SPARQL SELECT uit binnen de named graph van een DesignSpace.

    De named graph wordt als default graph behandeld — eenvoudige
    WHERE { ?s ?p ?o } queries werken zonder expliciete GRAPH-clausule.
    """
    graph_uri = named_graph_uri(named_graph)
    params = {"default-graph-uri": graph_uri}
    headers = {"Accept": "application/sparql-results+json"}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            _SPARQL_ENDPOINT,
            params=params,
            data={"query": query},
            headers=headers,
            timeout=30,
        )

    _raise_for_fuseki_error(response)

    data = response.json()
    bindings = data.get("results", {}).get("bindings", [])
    return [
        {k: v["value"] for k, v in row.items()}
        for row in bindings
    ]


_READONLY_QUERY_TYPES = ("select", "construct", "ask", "describe")


async def sparql_proxy_query(query: str, ds_id: str) -> dict[str, Any]:
    """Voert een read-only SPARQL query uit binnen de scope van een DesignSpace.

    Alle 5 named graphs van de DesignSpace worden als default graph toegevoegd,
    zodat de query alleen data van die DesignSpace kan zien (isolatie gegarandeerd).
    UPDATE/INSERT/DELETE queries worden geweigerd.
    """
    query_type = query.strip().split()[0].lower() if query.strip() else ""
    if query_type not in _READONLY_QUERY_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Alleen read-only SPARQL queries toegestaan (SELECT, CONSTRUCT, ASK, DESCRIBE). Ontvangen: '{query_type}'.",
        )

    graph_names = ["base", "asis", "decisions", "agents", "provenance"]
    params = [
        ("default-graph-uri", f"urn:valor:ds:{ds_id}/{g}")
        for g in graph_names
    ]
    headers = {"Accept": "application/sparql-results+json, application/ld+json;q=0.9, text/turtle;q=0.8"}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            _SPARQL_ENDPOINT,
            params=params,
            data={"query": query},
            headers=headers,
            timeout=30,
        )

    _raise_for_fuseki_error(response)
    return response.json()


async def sparql_update(update: str, named_graph: str) -> None:
    """Voert een SPARQL UPDATE uit.

    Gebruik named_graph_uri(named_graph) in GRAPH-clausules voor isolatie:
        INSERT DATA { GRAPH <urn:valor:ds:{id}> { <s> <p> <o> } }
    """
    logger.debug("sparql_update op graph %s", named_graph_uri(named_graph))
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _UPDATE_ENDPOINT,
            data={"update": update},
            auth=("admin", FUSEKI_ADMIN_PASSWORD),
            timeout=30,
        )

    _raise_for_fuseki_error(response)


_SHACL_ENDPOINT = f"{FUSEKI_URL}/{FUSEKI_DATASET}/shacl"

_SH_VALIDATION_REPORT = "http://www.w3.org/ns/shacl#ValidationReport"
_SH_CONFORMS = "http://www.w3.org/ns/shacl#conforms"
_SH_RESULT = "http://www.w3.org/ns/shacl#result"
_SH_RESULT_MESSAGE = "http://www.w3.org/ns/shacl#resultMessage"
_SH_SEVERITY = "http://www.w3.org/ns/shacl#resultSeverity"
_SH_VIOLATION = "http://www.w3.org/ns/shacl#Violation"


async def sparql_shacl_validate(named_graph: str, shapes_graph: str) -> list[str]:
    """Valideert een named graph met SHACL-shapes uit het dataset.

    Retourneert een lijst van violation-messages (leeg = geldig).
    Gebruikt de Fuseki fuseki:shacl endpoint met shapegraph= parameter.
    """
    graph_uri = named_graph_uri(named_graph)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            _SHACL_ENDPOINT,
            params={"graph": graph_uri, "shapegraph": shapes_graph},
            headers={"Accept": "application/ld+json"},
            auth=("admin", FUSEKI_ADMIN_PASSWORD),
            timeout=30,
        )

    if response.status_code >= 400:
        logger.error("SHACL-endpoint fout %s: %s", response.status_code, response.text[:300])
        return []  # Fail open: SHACL-endpoint niet beschikbaar

    try:
        report = response.json()
    except Exception:
        logger.error("SHACL-rapport niet parseerbaar: %s", response.text[:300])
        return []

    violations: list[str] = []
    for node in report:
        if _SH_VALIDATION_REPORT not in node.get("@type", []):
            continue
        conforms_entries = node.get(_SH_CONFORMS, [{}])
        if conforms_entries[0].get("@value", True):
            return []
        for result in node.get(_SH_RESULT, []):
            severity = result.get(_SH_SEVERITY, [{}])[0].get("@id", "")
            if severity != _SH_VIOLATION:
                continue
            for msg_entry in result.get(_SH_RESULT_MESSAGE, []):
                msg = msg_entry.get("@value", "")
                if msg:
                    violations.append(msg)

    return violations if violations else ([] if not report else ["SHACL-validatie mislukt (geen details)"])


async def sparql_select_global(query: str) -> list[dict[str, Any]]:
    """Voert een SPARQL SELECT uit op het gehele Fuseki-dataset (alle named graphs).

    Gebruik voor ontologie-queries zonder design space scope.
    """
    headers = {"Accept": "application/sparql-results+json"}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            _SPARQL_ENDPOINT,
            data={"query": query},
            headers=headers,
            timeout=30,
        )

    _raise_for_fuseki_error(response)

    data = response.json()
    bindings = data.get("results", {}).get("bindings", [])
    return [
        {k: v["value"] for k, v in row.items()}
        for row in bindings
    ]


async def initialize_design_space_graphs(ds_id: str, issue_uri: str) -> dict[str, str]:
    """Initialiseert de 5 named graphs voor een DesignSpace in Fuseki.

    Maakt de volgende named graphs aan via SPARQL CREATE:
    - base      : VALOR-O ontologie-referentie (read-only)
    - asis      : gedeelde as-is Tesserae
    - decisions : DecisionEpisodes + stemhistorie
    - agents    : AgentTesserae
    - provenance: PROV-O provenance trail
    """
    from app.ontology import VALOR_NS

    base = f"urn:valor:ds:{ds_id}/base"
    asis = f"urn:valor:ds:{ds_id}/asis"
    decisions = f"urn:valor:ds:{ds_id}/decisions"
    agents = f"urn:valor:ds:{ds_id}/agents"
    provenance = f"urn:valor:ds:{ds_id}/provenance"
    ds_uri = f"urn:valor:ds:{ds_id}"

    update = f"""
INSERT DATA {{
  GRAPH <{base}> {{
    <{ds_uri}> a <{VALOR_NS}DesignSpace> ;
      <{VALOR_NS}isAddressedInDesignSpace> <{issue_uri}> ;
      <{VALOR_NS}hasGraph> <{asis}> ;
      <{VALOR_NS}hasGraph> <{decisions}> ;
      <{VALOR_NS}hasGraph> <{agents}> ;
      <{VALOR_NS}hasGraph> <{provenance}> .
  }}
  GRAPH <{asis}> {{
    <{ds_uri}> <{VALOR_NS}graphType> "asis" .
  }}
  GRAPH <{decisions}> {{
    <{ds_uri}> <{VALOR_NS}graphType> "decisions" .
  }}
  GRAPH <{agents}> {{
    <{ds_uri}> <{VALOR_NS}graphType> "agents" .
  }}
  GRAPH <{provenance}> {{
    <{ds_uri}> <{VALOR_NS}graphType> "provenance" .
  }}
}}
"""

    await sparql_update(update, ds_id)

    return {
        "base": base,
        "asis": asis,
        "decisions": decisions,
        "agents": agents,
        "provenance": provenance,
    }


async def initialize_alternative_graph(
    ds_id: str, alt_id: str, name: str, description: str, creator_uri: str, created_at: str
) -> str:
    """Initialiseert een named graph voor een DesignAlternative in Fuseki.

    Schrijft een marker-triple in de graph en registreert de alternative in de base-graph.
    Retourneert de graph URI.
    """
    from app.ontology import VALOR_NS

    alt_uri = f"urn:valor:ds:{ds_id}/alternative/{alt_id}"
    base_graph = f"urn:valor:ds:{ds_id}/base"
    ds_uri = f"urn:valor:ds:{ds_id}"

    escaped_name = name.replace("\\", "\\\\").replace('"', '\\"')
    escaped_desc = (description or "").replace("\\", "\\\\").replace('"', '\\"')

    update = f"""INSERT DATA {{
  GRAPH <{alt_uri}> {{
    <{alt_uri}> <{VALOR_NS}graphType> "alternative" .
  }}
  GRAPH <{base_graph}> {{
    <{alt_uri}> a <{VALOR_NS}DesignAlternative> ;
      <{VALOR_NS}inDesignSpace> <{ds_uri}> ;
      <{VALOR_NS}alternativeName> "{escaped_name}"@nl ;
      <{VALOR_NS}alternativeDescription> "{escaped_desc}"@nl ;
      <{VALOR_NS}alternativeStatus> <{VALOR_NS}Active> ;
      <{VALOR_NS}createdBy> <{creator_uri}> ;
      <{VALOR_NS}createdAt> "{created_at}"^^<http://www.w3.org/2001/XMLSchema#dateTime> .
  }}
}}"""
    await sparql_update(update, ds_id)
    return alt_uri


async def sparql_construct(query: str, named_graph: str) -> str:
    """Voert een SPARQL CONSTRUCT uit binnen de named graph van een DesignSpace.

    Retourneert het resultaat als Turtle-string.
    """
    graph_uri = named_graph_uri(named_graph)
    params = {"default-graph-uri": graph_uri}
    headers = {"Accept": "text/turtle"}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            _SPARQL_ENDPOINT,
            params=params,
            data={"query": query},
            headers=headers,
            timeout=30,
        )

    _raise_for_fuseki_error(response)

    return response.text
