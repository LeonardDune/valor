"""Verificatiescript voor de dual-write fuseki_sync functies.

Gebruik:
    cd backend && python scripts/verify_fuseki_sync.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

FUSEKI_URL = os.getenv("FUSEKI_URL", "http://localhost:3030")
FUSEKI_DATASET = "valor"
FUSEKI_PASSWORD = os.getenv("FUSEKI_ADMIN_PASSWORD", "admin")
SPARQL = f"{FUSEKI_URL}/{FUSEKI_DATASET}/sparql"

TEST_THEME_ID = "test-theme-sync-verify"
TEST_FACTOR_ID = "test-factor-aaaaaaaa"
TEST_FACTOR2_ID = "test-factor-bbbbbbbb"
TEST_CLAIM_ID = "test-claim-cccccccc"


async def query_fuseki(sparql: str) -> list[dict]:
    from app.services.fuseki import _SPARQL_ENDPOINT
    async with httpx.AsyncClient() as client:
        r = await client.post(
            _SPARQL_ENDPOINT,
            data={"query": sparql},
            headers={"Accept": "application/sparql-results+json"},
            timeout=10,
        )
    r.raise_for_status()
    return r.json()["results"]["bindings"]


async def cleanup():
    """Verwijder testdata uit Fuseki."""
    from app.services.fuseki import _UPDATE_ENDPOINT
    graph = f"urn:valor:ds:{TEST_THEME_ID}"
    async with httpx.AsyncClient() as client:
        await client.post(
            _UPDATE_ENDPOINT,
            data={"update": f"DROP GRAPH <{graph}>"},
            auth=("admin", FUSEKI_PASSWORD),
            timeout=10,
        )


async def main():
    # Bootstrap ontologie-cache (laadt relaties vanuit Fuseki)
    from app.services.ontology_cache import load_ontology_cache
    print("Ontologie-cache laden...")
    await load_ontology_cache()

    from app.services.fuseki_sync import try_write_factor, try_write_claim
    from app.services.fuseki import named_graph_uri
    from app.ontology import VALOR_NS

    graph_uri = named_graph_uri(TEST_THEME_ID)

    # --- Test 1: try_write_factor ---
    print(f"\n[1] try_write_factor (factor_id={TEST_FACTOR_ID})")
    await try_write_factor(TEST_FACTOR_ID, "Testfactor Alpha", TEST_THEME_ID, "user-test-001")

    rows = await query_fuseki(f"""
        SELECT ?type ?content WHERE {{
          GRAPH <{graph_uri}> {{
            <urn:valor:tessera:{TEST_FACTOR_ID}> a ?type ;
              <{VALOR_NS}claimContent> ?content .
          }}
        }}
    """)
    if rows:
        print(f"  OK  Tessera aangemaakt: type={rows[0]['type']['value']}, content={rows[0]['content']['value']}")
    else:
        print("  FAIL  Geen Tessera gevonden in Fuseki!")
        sys.exit(1)

    # --- Test 2: tweede factor voor claim ---
    print(f"\n[2] try_write_factor (factor_id={TEST_FACTOR2_ID})")
    await try_write_factor(TEST_FACTOR2_ID, "Testfactor Beta", TEST_THEME_ID, "user-test-001")
    rows2 = await query_fuseki(f"""
        SELECT ?t WHERE {{
          GRAPH <{graph_uri}> {{
            <urn:valor:tessera:{TEST_FACTOR2_ID}> a <{VALOR_NS}Tessera> .
            BIND(<urn:valor:tessera:{TEST_FACTOR2_ID}> AS ?t)
          }}
        }}
    """)
    if rows2:
        print(f"  OK  Tweede Tessera aangemaakt")
    else:
        print("  FAIL  Tweede Tessera niet gevonden!")
        sys.exit(1)

    # --- Test 3: try_write_claim polarity "+" → supports ---
    print(f"\n[3] try_write_claim polarity '+' (claim_id={TEST_CLAIM_ID})")
    await try_write_claim(TEST_CLAIM_ID, TEST_FACTOR_ID, TEST_FACTOR2_ID, "+", TEST_THEME_ID)

    rows3 = await query_fuseki(f"""
        SELECT ?rel WHERE {{
          GRAPH <{graph_uri}> {{
            <urn:valor:tessera:{TEST_FACTOR_ID}> ?rel <urn:valor:tessera:{TEST_FACTOR2_ID}> .
          }}
        }}
    """)
    if rows3:
        print(f"  OK  Relatie aangemaakt: {rows3[0]['rel']['value']}")
        if "supports" in rows3[0]["rel"]["value"]:
            print(f"  OK  Relatie is correct 'supports'")
        else:
            print(f"  FAIL  Verwacht 'supports', got: {rows3[0]['rel']['value']}")
            sys.exit(1)
    else:
        print("  FAIL  Geen relatie gevonden in Fuseki!")
        sys.exit(1)

    # --- Test 4: try_write_claim polarity "-" → undermines ---
    print(f"\n[4] try_write_claim polarity '-' (claim_id={TEST_CLAIM_ID}-2)")
    await try_write_claim(TEST_CLAIM_ID + "-2", TEST_FACTOR2_ID, TEST_FACTOR_ID, "-", TEST_THEME_ID)

    rows4 = await query_fuseki(f"""
        SELECT ?rel WHERE {{
          GRAPH <{graph_uri}> {{
            <urn:valor:tessera:{TEST_FACTOR2_ID}> ?rel <urn:valor:tessera:{TEST_FACTOR_ID}> .
          }}
        }}
    """)
    if rows4 and "undermines" in rows4[0]["rel"]["value"]:
        print(f"  OK  Relatie is correct 'undermines': {rows4[0]['rel']['value']}")
    else:
        print(f"  FAIL  Verwacht 'undermines', got: {rows4}")
        sys.exit(1)

    # --- Cleanup ---
    print(f"\nTestdata opruimen (graph {graph_uri})...")
    await cleanup()
    print("Klaar.\n")
    print("Alle checks geslaagd.")


if __name__ == "__main__":
    asyncio.run(main())
