"""Verificatiescript voor US-3.2: SPARQL proxy access control.

Test de sparql_proxy_query functie direct tegen Fuseki:
- Scoping: query ziet alleen de 5 graphs van de opgegeven DesignSpace
- Isolatie: data van andere DesignSpaces is onzichtbaar
- Blokkering van UPDATE-queries

Gebruik:
    cd backend && FUSEKI_URL=http://localhost:3030 python scripts/verify_sparql_proxy_us32.py
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

DS_A = "verify-us32-ds-a"
DS_B = "verify-us32-ds-b"
ISSUE_A = "urn:valor:issue:us32-a"
ISSUE_B = "urn:valor:issue:us32-b"


async def cleanup(*ds_ids: str):
    graphs = [
        f"urn:valor:ds:{ds}/{g}"
        for ds in ds_ids
        for g in ["base", "asis", "decisions", "agents", "provenance"]
    ]
    drop = " ; ".join(f"DROP SILENT GRAPH <{g}>" for g in graphs)
    async with httpx.AsyncClient() as client:
        await client.post(
            UPDATE_ENDPOINT,
            data={"update": drop},
            auth=("admin", FUSEKI_PASSWORD),
            timeout=10,
        )


async def main():
    from app.services.fuseki import initialize_design_space_graphs, sparql_proxy_query
    from fastapi import HTTPException

    print("=== US-3.2 Verificatie: SPARQL proxy access control ===\n")
    await cleanup(DS_A, DS_B)

    print("1. Twee DesignSpaces initialiseren...")
    await initialize_design_space_graphs(DS_A, ISSUE_A)
    await initialize_design_space_graphs(DS_B, ISSUE_B)
    print("   OK\n")

    ok = True

    print("2. Query op DS_A ziet DS_A data...")
    result = await sparql_proxy_query(
        "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10", DS_A
    )
    bindings = result.get("results", {}).get("bindings", [])
    a_subjects = {b["s"]["value"] for b in bindings}
    ds_a_uri = f"urn:valor:ds:{DS_A}"
    ds_b_uri = f"urn:valor:ds:{DS_B}"
    if ds_a_uri in a_subjects:
        print(f"   [OK] DS_A URI aanwezig in resultaat")
    else:
        print(f"   [FAIL] DS_A URI niet gevonden: {a_subjects}")
        ok = False

    print("\n3. Query op DS_A ziet GEEN DS_B data...")
    if ds_b_uri not in a_subjects:
        print(f"   [OK] DS_B URI afwezig in DS_A query resultaat")
    else:
        print(f"   [FAIL] DS_B URI lekt in DS_A resultaat!")
        ok = False

    print("\n4. UPDATE query wordt geblokkeerd...")
    try:
        await sparql_proxy_query(
            "INSERT DATA { GRAPH <urn:test> { <a> <b> <c> } }", DS_A
        )
        print("   [FAIL] UPDATE niet geblokkeerd!")
        ok = False
    except HTTPException as e:
        if e.status_code == 400:
            print(f"   [OK] UPDATE geblokkeerd met 400: {e.detail[:60]}")
        else:
            print(f"   [FAIL] Verkeerde statuscode: {e.status_code}")
            ok = False

    print("\n5. ASK query werkt...")
    result = await sparql_proxy_query(
        f"ASK {{ <{ds_a_uri}> ?p ?o }}", DS_A
    )
    if result.get("boolean") is True:
        print("   [OK] ASK True voor bestaande triple")
    else:
        print(f"   [FAIL] ASK gaf: {result}")
        ok = False

    await cleanup(DS_A, DS_B)
    print("\n6. Testdata opgeruimd.")

    if ok:
        print("\n✓ US-3.2 verificatie geslaagd")
        sys.exit(0)
    else:
        print("\n✗ US-3.2 verificatie MISLUKT")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
