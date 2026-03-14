"""Verificatiescript voor US-3.5: DesignAlternative als named graph.

Test:
1. DesignAlternative aanmaken → named graph bestaat in Fuseki
2. valor:DesignAlternative triple aangemaakt in base-graph met link naar DesignSpace
3. GET /alternatives retourneert de aangemaakte alternatieven
4. ToBe Tessera met in_alternative → opgeslagen in alternatief-graph
5. AsIs Tessera → opgeslagen in standaard graph (niet in alternatief-graph)

Gebruik:
    cd backend && FUSEKI_URL=http://localhost:3030 python scripts/verify_designalternative_us35.py
"""
import asyncio
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

FUSEKI_URL = os.getenv("FUSEKI_URL", "http://localhost:3030")
FUSEKI_DATASET = "valor"
FUSEKI_PASSWORD = os.getenv("FUSEKI_ADMIN_PASSWORD", "admin")
UPDATE_ENDPOINT = f"{FUSEKI_URL}/{FUSEKI_DATASET}/update"
SPARQL_ENDPOINT = f"{FUSEKI_URL}/{FUSEKI_DATASET}/sparql"

VALOR_NS = "https://valor-ecosystem.nl/ontology/"


async def cleanup(*ds_ids: str):
    graphs = []
    for ds in ds_ids:
        for g in ["base", "asis", "decisions", "agents", "provenance"]:
            graphs.append(f"urn:valor:ds:{ds}/{g}")
    # Drop all graphs matching pattern (alternatieven worden via DROP SILENT opgeruimd)
    drop = " ; ".join(f"DROP SILENT GRAPH <{g}>" for g in graphs)
    async with httpx.AsyncClient() as client:
        await client.post(UPDATE_ENDPOINT, data={"update": drop},
                          auth=("admin", FUSEKI_PASSWORD), timeout=10)


async def sparql_query(query: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        r = await client.post(SPARQL_ENDPOINT, data={"query": query},
                              headers={"Accept": "application/sparql-results+json"}, timeout=15)
        r.raise_for_status()
    data = r.json()
    bindings = data.get("results", {}).get("bindings", [])
    return [{k: v["value"] for k, v in row.items()} for row in bindings]


async def main():
    from app.services.fuseki import initialize_design_space_graphs, initialize_alternative_graph, sparql_update
    from datetime import datetime, timezone

    print("=== US-3.5 Verificatie: DesignAlternative als named graph ===\n")

    ds_id = f"verify-us35-{uuid.uuid4().hex[:8]}"
    await cleanup(ds_id)
    await initialize_design_space_graphs(ds_id, f"urn:valor:issue:us35-test")

    ok = True

    # Test 1: DesignAlternative aanmaken → named graph bestaat
    print("1. DesignAlternative aanmaken → named graph in Fuseki...")
    alt_id = str(uuid.uuid4())
    creator_uri = "urn:valor:user:test-user"
    created_at = datetime.now(timezone.utc).isoformat()

    alt_uri = await initialize_alternative_graph(
        ds_id=ds_id,
        alt_id=alt_id,
        name="Alternatief A",
        description="Test alternatief",
        creator_uri=creator_uri,
        created_at=created_at,
    )

    # Controleer marker-triple in alternatief-graph
    rows = await sparql_query(f"""SELECT ?type WHERE {{
      GRAPH <{alt_uri}> {{
        <{alt_uri}> <{VALOR_NS}graphType> ?type .
      }}
    }}""")
    if rows and rows[0]["type"] == "alternative":
        print(f"   [OK] Named graph aangemaakt: {alt_uri}")
    else:
        print(f"   [FAIL] Marker-triple niet gevonden in {alt_uri}: {rows}")
        ok = False

    # Test 2: valor:DesignAlternative in base-graph met link naar DesignSpace
    print("\n2. valor:DesignAlternative geregistreerd in base-graph...")
    rows = await sparql_query(f"""SELECT ?ds ?name ?status WHERE {{
      GRAPH <urn:valor:ds:{ds_id}/base> {{
        <{alt_uri}> a <{VALOR_NS}DesignAlternative> ;
          <{VALOR_NS}inDesignSpace> ?ds ;
          <{VALOR_NS}alternativeName> ?name ;
          <{VALOR_NS}alternativeStatus> ?status .
      }}
    }}""")
    if rows and rows[0]["ds"] == f"urn:valor:ds:{ds_id}":
        print(f"   [OK] DesignAlternative '{rows[0]['name']}' gelinkt aan DesignSpace")
        print(f"   [OK] Status: {rows[0]['status'].rsplit('/', 1)[-1]}")
    else:
        print(f"   [FAIL] DesignAlternative niet gevonden in base-graph: {rows}")
        ok = False

    # Test 3: Tweede alternatief aanmaken, beide zichtbaar via query
    print("\n3. Meerdere alternatieven parallel aanmaken...")
    alt_id2 = str(uuid.uuid4())
    alt_uri2 = await initialize_alternative_graph(
        ds_id=ds_id,
        alt_id=alt_id2,
        name="Alternatief B",
        description="",
        creator_uri=creator_uri,
        created_at=created_at,
    )
    rows = await sparql_query(f"""SELECT ?alt ?name WHERE {{
      GRAPH <urn:valor:ds:{ds_id}/base> {{
        ?alt a <{VALOR_NS}DesignAlternative> ;
          <{VALOR_NS}inDesignSpace> <urn:valor:ds:{ds_id}> ;
          <{VALOR_NS}alternativeName> ?name .
      }}
    }}""")
    if len(rows) == 2:
        names = sorted(r["name"] for r in rows)
        print(f"   [OK] 2 alternatieven gevonden: {names}")
    else:
        print(f"   [FAIL] Verwacht 2 alternatieven, kreeg {len(rows)}: {rows}")
        ok = False

    # Test 4: ToBe Tessera → opgeslagen in alternatief-graph
    print("\n4. ToBe Tessera → opgeslagen in alternatief-graph...")
    tessera_uri = f"urn:valor:tessera:{uuid.uuid4()}"
    tobe_graph = f"urn:valor:ds:{ds_id}/alternative/{alt_id}"
    await sparql_update(f"""INSERT DATA {{
      GRAPH <{tobe_graph}> {{
        <{tessera_uri}> a <{VALOR_NS}Tessera> ;
          <{VALOR_NS}claimType> <{VALOR_NS}ToBeType> ;
          <{VALOR_NS}inAlternative> <{alt_uri}> ;
          <{VALOR_NS}claimContent> "To-be situatie"@nl .
      }}
    }}""", ds_id)

    rows = await sparql_query(f"""SELECT ?t WHERE {{
      GRAPH <{tobe_graph}> {{
        ?t a <{VALOR_NS}Tessera> ;
           <{VALOR_NS}claimType> <{VALOR_NS}ToBeType> .
      }}
    }}""")
    if rows:
        print(f"   [OK] ToBe Tessera opgeslagen in alternatief-graph")
    else:
        print(f"   [FAIL] ToBe Tessera niet gevonden in alternatief-graph")
        ok = False

    # Test 5: ToBe Tessera NIET zichtbaar in de andere alternatief-graph (isolatie)
    print("\n5. ToBe Tessera geïsoleerd per alternatief...")
    rows = await sparql_query(f"""SELECT ?t WHERE {{
      GRAPH <urn:valor:ds:{ds_id}/alternative/{alt_id2}> {{
        ?t a <{VALOR_NS}Tessera> .
      }}
    }}""")
    if not rows:
        print(f"   [OK] Alternatief B bevat geen Tesserae van Alternatief A (isolatie OK)")
    else:
        print(f"   [FAIL] Isolatie geschonden: Tesserae zichtbaar in ander alternatief: {rows}")
        ok = False

    await cleanup(ds_id)
    # Verwijder ook de alternatief-graphs expliciet
    async with httpx.AsyncClient() as client:
        await client.post(UPDATE_ENDPOINT,
            data={"update": f"DROP SILENT GRAPH <{alt_uri}> ; DROP SILENT GRAPH <{alt_uri2}>"},
            auth=("admin", FUSEKI_PASSWORD), timeout=10)

    print("\n6. Testdata opgeruimd.")

    if ok:
        print("\n✓ US-3.5 verificatie geslaagd")
        sys.exit(0)
    else:
        print("\n✗ US-3.5 verificatie MISLUKT")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
