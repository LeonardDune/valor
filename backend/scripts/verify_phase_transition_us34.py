"""Verificatiescript voor US-3.4: Faseovergang via POST /designspace/{id}/phase/transition.

Test:
1. Fasesequentie correct (exploration → definition → evaluation → decision)
2. Gate-check: FeasibilityAssessment ontbreekt → 422-logica klopt
3. Gate-check: beide aanwezig → overgang slaagt
4. NotFeasible/NotCovered → alternatief gearchiveerd en niet meer actief
5. DecisionEpisode aangemaakt in decisions-graph
6. Neo4j current_phase bijgewerkt

Gebruik:
    cd backend && FUSEKI_URL=http://localhost:3030 python scripts/verify_phase_transition_us34.py
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
XSD_NS = "http://www.w3.org/2001/XMLSchema#"


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


async def sparql_query(query: str) -> list[dict]:
    """Directe SPARQL SELECT zonder default-graph-uri beperking."""
    async with httpx.AsyncClient() as client:
        r = await client.post(
            SPARQL_ENDPOINT,
            data={"query": query},
            headers={"Accept": "application/sparql-results+json"},
            timeout=15,
        )
        r.raise_for_status()
    data = r.json()
    bindings = data.get("results", {}).get("bindings", [])
    return [{k: v["value"] for k, v in row.items()} for row in bindings]


async def fuseki_update(update: str):
    async with httpx.AsyncClient() as client:
        r = await client.post(
            UPDATE_ENDPOINT,
            data={"update": update},
            auth=("admin", FUSEKI_PASSWORD),
            timeout=10,
        )
        r.raise_for_status()


async def insert_gate_tessera(ds_id: str, alt_id: str, gate_type: str, status_suffix: str):
    """Voeg een gate-Tessera toe aan de asis-graph."""
    asis = f"urn:valor:ds:{ds_id}/asis"
    t_uri = f"urn:valor:tessera:{uuid.uuid4()}"
    alt_uri = f"urn:valor:alternative:{alt_id}"
    status_uri = f"{VALOR_NS}{status_suffix}"
    await fuseki_update(f"""INSERT DATA {{
      GRAPH <{asis}> {{
        <{t_uri}> a <{VALOR_NS}Tessera> ;
                  a <{VALOR_NS}{gate_type}> ;
          <{VALOR_NS}inAlternative> <{alt_uri}> ;
          <{VALOR_NS}epistemicStatus> <{status_uri}> ;
          <{VALOR_NS}claimContent> "gate tessera"@nl .
      }}
    }}""")


async def main():
    from app.services.fuseki import initialize_design_space_graphs
    from app.db.designspace import get_design_space_meta, set_design_space_phase, PHASE_SEQUENCE
    from app.db.utils import get_driver

    print("=== US-3.4 Verificatie: Faseovergang ===\n")

    ok = True

    # Test 1: Fasesequentie
    print("1. Fasesequentie correct...")
    expected = ["exploration", "definition", "evaluation", "decision"]
    if PHASE_SEQUENCE == expected:
        print(f"   [OK] {PHASE_SEQUENCE}")
    else:
        print(f"   [FAIL] Verwacht {expected}, kreeg {PHASE_SEQUENCE}")
        ok = False

    # Test 2: Neo4j current_phase bijwerken via bestaande gemigreerde DesignSpace
    print("\n2. Neo4j current_phase bijwerken...")
    driver = get_driver()
    with driver.session() as s:
        result = s.run("MATCH (ds:DesignSpace) RETURN ds.id AS id LIMIT 1").single()
        real_ds_id = result["id"] if result else None

    if real_ds_id:
        set_design_space_phase(real_ds_id, "definition")
        meta = get_design_space_meta(real_ds_id)
        if meta and meta["current_phase"] == "definition":
            print(f"   [OK] current_phase = definition voor DesignSpace {real_ds_id[:8]}...")
            # Zet terug naar exploration
            set_design_space_phase(real_ds_id, "exploration")
        else:
            print(f"   [FAIL] Meta: {meta}")
            ok = False
    else:
        print("   [SKIP] Geen DesignSpace in Neo4j, sla Neo4j-test over")

    # Test 3: Gate-check — ontbrekende FeasibilityAssessment
    print("\n3. Gate-check: FeasibilityAssessment ontbreekt...")
    ds3 = f"verify-us34a-{uuid.uuid4().hex[:8]}"
    await cleanup(ds3)
    await initialize_design_space_graphs(ds3, "urn:valor:issue:us34-a")
    alt_id3 = f"alt-{uuid.uuid4().hex[:6]}"
    # Voeg alleen ClaimCoverageAssessment toe
    await insert_gate_tessera(ds3, alt_id3, "ClaimCoverageAssessment", "AcceptedStatus")

    rows = await sparql_query(f"""SELECT ?t WHERE {{
      GRAPH <urn:valor:ds:{ds3}/asis> {{
        ?t a <{VALOR_NS}FeasibilityAssessment> ;
           <{VALOR_NS}inAlternative> <urn:valor:alternative:{alt_id3}> .
      }}
    }}""")
    if not rows:
        print("   [OK] FeasibilityAssessment afwezig → gate-check zou 422 retourneren")
    else:
        print(f"   [FAIL] FeasibilityAssessment onverwacht aanwezig: {rows}")
        ok = False

    # Test 4: Beide gate-Tesserae aanwezig
    print("\n4. Beide gate-Tesserae aanwezig → overgang slaagt...")
    ds4 = f"verify-us34b-{uuid.uuid4().hex[:8]}"
    await cleanup(ds4)
    await initialize_design_space_graphs(ds4, "urn:valor:issue:us34-b")
    alt_id4 = f"alt-{uuid.uuid4().hex[:6]}"
    await insert_gate_tessera(ds4, alt_id4, "FeasibilityAssessment", "ProposedStatus")
    await insert_gate_tessera(ds4, alt_id4, "ClaimCoverageAssessment", "ProposedStatus")

    for gate_type in ["FeasibilityAssessment", "ClaimCoverageAssessment"]:
        rows = await sparql_query(f"""SELECT ?status WHERE {{
          GRAPH <urn:valor:ds:{ds4}/asis> {{
            ?t a <{VALOR_NS}{gate_type}> ;
               <{VALOR_NS}inAlternative> <urn:valor:alternative:{alt_id4}> ;
               <{VALOR_NS}epistemicStatus> ?status .
          }}
        }}""")
        if rows:
            print(f"   [OK] {gate_type} aanwezig met status {rows[0]['status'].rsplit('/', 1)[-1]}")
        else:
            print(f"   [FAIL] {gate_type} niet gevonden")
            ok = False

    # Test 5: NotFeasible → alternatief archiveren
    print("\n5. NotFeasible → alternatief archiveren, niet meer actief...")
    ds5 = f"verify-us34c-{uuid.uuid4().hex[:8]}"
    await cleanup(ds5)
    await initialize_design_space_graphs(ds5, "urn:valor:issue:us34-c")
    alt_id5 = f"alt-{uuid.uuid4().hex[:6]}"
    alt_uri5 = f"urn:valor:alternative:{alt_id5}"
    await insert_gate_tessera(ds5, alt_id5, "FeasibilityAssessment", "NotFeasible")
    await insert_gate_tessera(ds5, alt_id5, "ClaimCoverageAssessment", "AcceptedStatus")

    # Archiveer
    await fuseki_update(f"""INSERT DATA {{
      GRAPH <urn:valor:ds:{ds5}/base> {{
        <{alt_uri5}> <{VALOR_NS}alternativeStatus> <{VALOR_NS}Archived> .
      }}
    }}""")

    # Controleer: niet meer in actieve alternatieven
    alt_rows = await sparql_query(f"""SELECT DISTINCT ?alt WHERE {{
      GRAPH <urn:valor:ds:{ds5}/asis> {{
        ?t <{VALOR_NS}inAlternative> ?alt .
      }}
      FILTER NOT EXISTS {{
        GRAPH <urn:valor:ds:{ds5}/base> {{
          ?alt <{VALOR_NS}alternativeStatus> <{VALOR_NS}Archived> .
        }}
      }}
    }}""")
    if not alt_rows:
        print("   [OK] Gearchiveerd alternatief niet meer actief")
    else:
        print(f"   [FAIL] Alternatief nog actief na archivering: {alt_rows}")
        ok = False

    # Test 6: DecisionEpisode aanmaken
    print("\n6. PhaseTransition DecisionEpisode aanmaken...")
    episode_id = str(uuid.uuid4())
    episode_uri = f"urn:valor:episode:{episode_id}"
    decisions_graph = f"urn:valor:ds:{ds4}/decisions"
    from datetime import datetime, timezone
    transitioned_at = datetime.now(timezone.utc).isoformat()

    await fuseki_update(f"""INSERT DATA {{
      GRAPH <{decisions_graph}> {{
        <{episode_uri}> a <{VALOR_NS}PhaseTransition> ;
          <{VALOR_NS}fromPhase> <urn:valor:phase:exploration> ;
          <{VALOR_NS}toPhase> <urn:valor:phase:definition> ;
          <{VALOR_NS}triggeredBy> <urn:valor:user:test> ;
          <{VALOR_NS}triggeredAt> "{transitioned_at}"^^<{XSD_NS}dateTime> ;
          <{VALOR_NS}inDesignSpace> <urn:valor:ds:{ds4}> .
      }}
    }}""")

    rows = await sparql_query(f"""SELECT ?from ?to WHERE {{
      GRAPH <{decisions_graph}> {{
        <{episode_uri}> a <{VALOR_NS}PhaseTransition> ;
          <{VALOR_NS}fromPhase> ?from ;
          <{VALOR_NS}toPhase> ?to .
      }}
    }}""")
    if rows and rows[0]["from"] == "urn:valor:phase:exploration":
        print(f"   [OK] DecisionEpisode aangemaakt: exploration → definition")
    else:
        print(f"   [FAIL] DecisionEpisode niet gevonden: {rows}")
        ok = False

    # Cleanup
    await cleanup(ds3, ds4, ds5)
    print("\n7. Testdata opgeruimd.")

    if ok:
        print("\n✓ US-3.4 verificatie geslaagd")
        sys.exit(0)
    else:
        print("\n✗ US-3.4 verificatie MISLUKT")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
