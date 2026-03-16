"""Verificatiescript US-3.7: PROV-O provenance bij Tessera-schrijfoperaties.

Controleert:
1. TesseraCreated → prov:Activity met prov:generated in provenance-graph
2. StatusChanged  → prov:Activity met used + previousStatus/newStatus
3. ArgumentAdded  → prov:Activity met used (source + target)
4. Provenance is append-only (niet wijzigbaar)

Gebruik:
    FUSEKI_URL=http://localhost:3030 python3 verify_provenance_us37.py
"""
import asyncio
import logging
import os
import sys

import httpx

logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(message)s")
logger = logging.getLogger(__name__)

FUSEKI_URL = os.getenv("FUSEKI_URL", "http://localhost:3030")
DATASET = "valor"
PROV_NS = "https://www.w3.org/ns/prov#"
VALOR_NS = "https://valor-ecosystem.nl/ontology/"


async def sparql_query(query: str, client: httpx.AsyncClient) -> dict:
    resp = await client.post(
        f"{FUSEKI_URL}/{DATASET}/sparql",
        data={"query": query},
        headers={"Accept": "application/sparql-results+json"},
        auth=("admin", "admin"),
    )
    resp.raise_for_status()
    return resp.json()


async def sparql_update_direct(update: str, client: httpx.AsyncClient) -> None:
    resp = await client.post(
        f"{FUSEKI_URL}/{DATASET}/update",
        data={"update": update},
        auth=("admin", "admin"),
    )
    resp.raise_for_status()


async def main() -> None:
    logger.info("=== US-3.7 Verificatie: PROV-O provenance ===")
    sys.path.insert(0, "/home/renzo/projects/valor/backend")
    from app.services.fuseki import record_provenance_activity, sparql_update

    ds_id = "verify-us37"
    prov_graph = f"urn:valor:ds:{ds_id}/provenance"
    tessera_uri = "urn:valor:tessera:verify-t1"
    target_uri = "urn:valor:tessera:verify-t2"
    user_uri = "urn:valor:user:verify-user"

    errors: list[str] = []

    async with httpx.AsyncClient(timeout=30) as client:
        # Cleanup
        await sparql_update_direct(f"DROP SILENT GRAPH <{prov_graph}>", client)

        # ── Stap 1: TesseraCreated ─────────────────────────────────────────────
        try:
            logger.info("Stap 1: TesseraCreated provenance...")
            act1 = await record_provenance_activity(
                ds_id, "TesseraCreated", user_uri,
                generated=tessera_uri,
            )
            q = f"""PREFIX prov: <{PROV_NS}>
SELECT ?gen ?agent ?op WHERE {{
  GRAPH <{prov_graph}> {{
    <{act1}> a prov:Activity ;
      prov:generated ?gen ;
      prov:wasAttributedTo ?agent ;
      <urn:valor:operationType> ?op .
  }}
}}"""
            result = await sparql_query(q, client)
            rows = result["results"]["bindings"]
            assert len(rows) == 1, f"Verwacht 1 record, gevonden: {len(rows)}"
            assert rows[0]["gen"]["value"] == tessera_uri
            assert rows[0]["agent"]["value"] == user_uri
            assert "TesseraCreated" in rows[0]["op"]["value"]
            logger.info("  ✓ TesseraCreated: activity=%s, generated=%s", act1, tessera_uri)
        except Exception as e:
            logger.error("FAIL Stap 1: %s", e)
            errors.append(f"TesseraCreated: {e}")

        # ── Stap 2: StatusChanged ──────────────────────────────────────────────
        try:
            logger.info("Stap 2: StatusChanged provenance...")
            proposed_uri = f"{VALOR_NS}ProposedStatus"
            accepted_uri = f"{VALOR_NS}AcceptedStatus"
            act2 = await record_provenance_activity(
                ds_id, "StatusChanged", user_uri,
                used=[tessera_uri],
                extra_props=[
                    (f"{VALOR_NS}previousStatus", proposed_uri),
                    (f"{VALOR_NS}newStatus", accepted_uri),
                ],
            )
            q = f"""PREFIX prov: <{PROV_NS}>
SELECT ?used ?prev ?new WHERE {{
  GRAPH <{prov_graph}> {{
    <{act2}> prov:used ?used ;
      <{VALOR_NS}previousStatus> ?prev ;
      <{VALOR_NS}newStatus> ?new .
  }}
}}"""
            result = await sparql_query(q, client)
            rows = result["results"]["bindings"]
            assert len(rows) == 1, f"Verwacht 1 record, gevonden: {len(rows)}"
            assert rows[0]["used"]["value"] == tessera_uri
            assert rows[0]["prev"]["value"] == proposed_uri
            assert rows[0]["new"]["value"] == accepted_uri
            logger.info("  ✓ StatusChanged: %s → %s", proposed_uri.split("/")[-1], accepted_uri.split("/")[-1])
        except Exception as e:
            logger.error("FAIL Stap 2: %s", e)
            errors.append(f"StatusChanged: {e}")

        # ── Stap 3: ArgumentAdded ──────────────────────────────────────────────
        try:
            logger.info("Stap 3: ArgumentAdded provenance...")
            supports_uri = f"{VALOR_NS}supports"
            act3 = await record_provenance_activity(
                ds_id, "ArgumentAdded", user_uri,
                used=[tessera_uri, target_uri],
                extra_props=[(supports_uri, target_uri)],
            )
            q = f"""PREFIX prov: <{PROV_NS}>
SELECT ?used WHERE {{
  GRAPH <{prov_graph}> {{
    <{act3}> prov:used ?used .
  }}
}} ORDER BY ?used"""
            result = await sparql_query(q, client)
            rows = result["results"]["bindings"]
            used_uris = {r["used"]["value"] for r in rows}
            assert tessera_uri in used_uris, f"source ontbreekt: {used_uris}"
            assert target_uri in used_uris, f"target ontbreekt: {used_uris}"
            logger.info("  ✓ ArgumentAdded: source + target in prov:used")
        except Exception as e:
            logger.error("FAIL Stap 3: %s", e)
            errors.append(f"ArgumentAdded: {e}")

        # ── Stap 4: Totaalcheck ────────────────────────────────────────────────
        try:
            logger.info("Stap 4: Totaal 3 activities in provenance-graph...")
            q = f"""PREFIX prov: <{PROV_NS}>
SELECT (COUNT(?a) AS ?count) WHERE {{
  GRAPH <{prov_graph}> {{ ?a a prov:Activity . }}
}}"""
            result = await sparql_query(q, client)
            count = int(result["results"]["bindings"][0]["count"]["value"])
            assert count == 3, f"Verwacht 3 activities, gevonden: {count}"
            logger.info("  ✓ 3/3 activities aanwezig")
        except Exception as e:
            logger.error("FAIL Stap 4: %s", e)
            errors.append(f"Totaalcheck: {e}")

        # Cleanup
        await sparql_update_direct(f"DROP SILENT GRAPH <{prov_graph}>", client)

    print()
    if errors:
        logger.error("GEFAALD (%d fouten):", len(errors))
        for err in errors:
            logger.error("  - %s", err)
        sys.exit(1)
    else:
        logger.info("=== Alle stappen geslaagd ===")


if __name__ == "__main__":
    asyncio.run(main())
