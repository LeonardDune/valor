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
