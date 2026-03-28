"""Migratiescript: kopieer asis-graphs naar baseline-graphs en alternative-graphs naar scenario-graphs.

Non-destructief: originele graphs (/asis, /alternative/{id}) blijven bestaan.

Gebruik:
    python scripts/migrate_asis_to_baseline.py

Vereist:
    - FUSEKI_URL (default: http://localhost:3030)
    - FUSEKI_ADMIN_PASSWORD (default: admin)
    - NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD voor DesignSpace-ophaling
"""
import asyncio
import logging
import os

import httpx
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

FUSEKI_URL = os.getenv("FUSEKI_URL", "http://localhost:3030")
FUSEKI_DATASET = "valor"
FUSEKI_ADMIN_PASSWORD = os.getenv("FUSEKI_ADMIN_PASSWORD", "admin")
_UPDATE_ENDPOINT = f"{FUSEKI_URL}/{FUSEKI_DATASET}/update"

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")


def get_all_design_space_ids() -> list[str]:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    with driver.session() as session:
        result = session.run("MATCH (ds:DesignSpace) RETURN ds.id AS id")
        ids = [r["id"] for r in result if r["id"]]
    driver.close()
    return ids


def get_scenario_ids_for_design_space(ds_id: str) -> list[str]:
    """Haal scenario/alternative IDs op via Neo4j als die beschikbaar zijn — anders via SPARQL."""
    return []


async def sparql_update(update: str) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _UPDATE_ENDPOINT,
            data={"update": update},
            auth=("admin", FUSEKI_ADMIN_PASSWORD),
            timeout=60,
        )
    if response.status_code >= 400:
        raise RuntimeError(f"Fuseki fout {response.status_code}: {response.text[:300]}")


async def sparql_select_global(query: str) -> list[dict]:
    sparql_endpoint = f"{FUSEKI_URL}/{FUSEKI_DATASET}/sparql"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            sparql_endpoint,
            data={"query": query},
            headers={"Accept": "application/sparql-results+json"},
            timeout=60,
        )
    if response.status_code >= 400:
        raise RuntimeError(f"Fuseki fout {response.status_code}: {response.text[:300]}")
    data = response.json()
    bindings = data.get("results", {}).get("bindings", [])
    return [{k: v["value"] for k, v in row.items()} for row in bindings]


async def copy_graph(source_uri: str, target_uri: str) -> None:
    """Kopieert alle triples van source_uri naar target_uri (additief)."""
    update = f"ADD <{source_uri}> TO <{target_uri}>"
    await sparql_update(update)


async def get_alternative_ids_for_ds(ds_id: str) -> list[str]:
    """Zoek alle alternative-graph IDs voor een DesignSpace via Fuseki."""
    base_graph = f"urn:valor:ds:{ds_id}/base"
    rows = await sparql_select_global(
        f"""SELECT ?alt WHERE {{
          GRAPH <{base_graph}> {{
            ?alt a <https://valor-ecosystem.nl/ontology/DesignAlternative> ;
                 <https://valor-ecosystem.nl/ontology/inDesignSpace> <urn:valor:ds:{ds_id}> .
          }}
        }}"""
    )
    alt_ids = []
    for row in rows:
        alt_uri = row.get("alt", "")
        prefix = f"urn:valor:ds:{ds_id}/alternative/"
        if alt_uri.startswith(prefix):
            alt_ids.append(alt_uri[len(prefix):])
    return alt_ids


async def migrate_design_space(ds_id: str) -> None:
    asis_graph = f"urn:valor:ds:{ds_id}/asis"
    baseline_graph = f"urn:valor:ds:{ds_id}/baseline"

    logger.info("DS %s: kopieer %s → %s", ds_id, asis_graph, baseline_graph)
    try:
        await copy_graph(asis_graph, baseline_graph)
        logger.info("DS %s: baseline-graph aangemaakt", ds_id)
    except RuntimeError as e:
        logger.warning("DS %s: baseline-kopie mislukt: %s", ds_id, e)

    alt_ids = await get_alternative_ids_for_ds(ds_id)
    for alt_id in alt_ids:
        alt_graph = f"urn:valor:ds:{ds_id}/alternative/{alt_id}"
        scenario_graph = f"urn:valor:ds:{ds_id}/scenario/{alt_id}"
        logger.info("DS %s: kopieer %s → %s", ds_id, alt_graph, scenario_graph)
        try:
            await copy_graph(alt_graph, scenario_graph)
            logger.info("DS %s: scenario-graph %s aangemaakt", ds_id, alt_id)
        except RuntimeError as e:
            logger.warning("DS %s alt %s: scenario-kopie mislukt: %s", ds_id, alt_id, e)


async def main() -> None:
    logger.info("Start migratie asis → baseline, alternative → scenario")

    ds_ids = get_all_design_space_ids()
    logger.info("Gevonden DesignSpaces: %d", len(ds_ids))

    for ds_id in ds_ids:
        await migrate_design_space(ds_id)

    logger.info("Migratie voltooid")


if __name__ == "__main__":
    asyncio.run(main())
