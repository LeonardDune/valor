"""Verificatiescript voor US-3.1: DesignSpace named graph initialisatie.

Gebruik:
    cd backend && python scripts/verify_designspace_us31.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

FUSEKI_URL = os.getenv("FUSEKI_URL", "http://localhost:3030")
FUSEKI_DATASET = "valor"
FUSEKI_PASSWORD = os.getenv("FUSEKI_ADMIN_PASSWORD", "admin")
UPDATE_ENDPOINT = f"{FUSEKI_URL}/{FUSEKI_DATASET}/update"
SPARQL_ENDPOINT = f"{FUSEKI_URL}/{FUSEKI_DATASET}/sparql"

TEST_DS_ID = "verify-us31-test-ds"
TEST_ISSUE_URI = "urn:valor:issue:test-us31"


async def query_named_graphs() -> list[str]:
    sparql = "SELECT DISTINCT ?g WHERE { GRAPH ?g { } }"
    async with httpx.AsyncClient() as client:
        r = await client.post(
            SPARQL_ENDPOINT,
            data={"query": sparql},
            headers={"Accept": "application/sparql-results+json"},
            timeout=10,
        )
    r.raise_for_status()
    return [row["g"]["value"] for row in r.json()["results"]["bindings"]]


async def query_base_graph(ds_id: str) -> list[dict]:
    base_uri = f"urn:valor:ds:{ds_id}/base"
    sparql = f"SELECT ?p ?o WHERE {{ GRAPH <{base_uri}> {{ <urn:valor:ds:{ds_id}> ?p ?o }} }}"
    async with httpx.AsyncClient() as client:
        r = await client.post(
            SPARQL_ENDPOINT,
            data={"query": sparql},
            headers={"Accept": "application/sparql-results+json"},
            timeout=10,
        )
    r.raise_for_status()
    return r.json()["results"]["bindings"]


async def cleanup(ds_id: str):
    graphs = [f"urn:valor:ds:{ds_id}/{g}" for g in ["base", "asis", "decisions", "agents", "provenance"]]
    drop = " ; ".join(f"DROP SILENT GRAPH <{g}>" for g in graphs)
    async with httpx.AsyncClient() as client:
        await client.post(
            UPDATE_ENDPOINT,
            data={"update": drop},
            auth=("admin", FUSEKI_PASSWORD),
            timeout=10,
        )


async def main():
    from app.services.fuseki import initialize_design_space_graphs

    print(f"=== US-3.1 Verificatie: DesignSpace named graphs ===\n")

    await cleanup(TEST_DS_ID)

    print("1. Initialiseer named graphs...")
    named_graphs = await initialize_design_space_graphs(TEST_DS_ID, TEST_ISSUE_URI)
    print(f"   Aangemaakt: {list(named_graphs.keys())}")

    print("\n2. Controleer named graphs bestaan in Fuseki...")
    all_graphs = await query_named_graphs()
    expected = [named_graphs[g] for g in ["base", "asis", "decisions", "agents", "provenance"]]
    ok = True
    for g in expected:
        exists = g in all_graphs
        mark = "OK" if exists else "FAIL"
        print(f"   [{mark}] {g}")
        if not exists:
            ok = False

    print("\n3. Controleer metadata in base-graph...")
    triples = await query_base_graph(TEST_DS_ID)
    print(f"   Triples in base: {len(triples)}")
    for t in triples:
        print(f"   - {t['p']['value'].split('/')[-1]} → {t['o']['value']}")

    await cleanup(TEST_DS_ID)
    print(f"\n4. Testdata opgeruimd.")

    if ok and len(triples) >= 5:
        print("\n✓ US-3.1 verificatie geslaagd")
        sys.exit(0)
    else:
        print("\n✗ US-3.1 verificatie MISLUKT")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
