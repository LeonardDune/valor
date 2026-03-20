"""Fix-script: voeg valor:baseId toe aan alle bestaande Tesserae in Fuseki (US-11.2).

Bestaande Tesserae missen mogelijk de valor:baseId property:
- Tesserae aangemaakt via migratiescript: URI-suffix = FactorVersion.id (version_id)
- Tesserae aangemaakt via dual-write: URI-suffix = FactorBase.id (base_id)

Dit script:
1. Vindt alle Tesserae zonder valor:baseId in Fuseki
2. Zoekt in Neo4j de bijbehorende base_id op (via version_id of base_id lookup)
3. Voegt valor:baseId toe als property (idempotent via INSERT WHERE NOT EXISTS)

Na afloop kunnen de SPARQL-queries in fuseki_knowledge.py correct werken.

Gebruik:
    cd backend
    FUSEKI_URL=http://localhost:3030 python scripts/fix_tessera_base_ids.py

    # Dry-run (geen schrijfoperaties, alleen rapportage):
    FUSEKI_URL=http://localhost:3030 python scripts/fix_tessera_base_ids.py --dry-run
"""
import asyncio
import sys
import os
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

VALOR_NS = "https://valor-ecosystem.nl/ontology/"
TESSERA_PREFIX = "urn:valor:tessera:"


# ---------------------------------------------------------------------------
# Fuseki: alle Tesserae zonder baseId ophalen
# ---------------------------------------------------------------------------

async def _get_tesserae_without_base_id() -> list[dict]:
    """Geeft alle Tesserae zonder valor:baseId, met hun graph-URI."""
    from app.services.fuseki import sparql_select_global
    rows = await sparql_select_global(f"""
SELECT ?tessera ?graph WHERE {{
  GRAPH ?graph {{ ?tessera a <{VALOR_NS}Tessera> }}
  FILTER NOT EXISTS {{
    GRAPH ?graph {{ ?tessera <{VALOR_NS}baseId> ?bid }}
  }}
  FILTER(STRSTARTS(STR(?graph), "urn:valor:ds:"))
}}
""")
    return rows


# ---------------------------------------------------------------------------
# Neo4j: base_id opzoeken voor een gegeven URI-suffix
# ---------------------------------------------------------------------------

def _resolve_base_id_neo4j(suffix: str) -> str | None:
    """Zoekt de base_id op in Neo4j voor een gegeven URI-suffix.

    Suffix kan een FactorVersion.id, FactorBase.id, ClaimVersion.id of ClaimBase.id zijn.
    """
    from app.db.utils import get_driver
    driver = get_driver()
    query = """
    OPTIONAL MATCH (fv:FactorVersion {id: $suffix}) WITH fv
    OPTIONAL MATCH (fb:FactorBase {id: $suffix})
    OPTIONAL MATCH (cv:ClaimVersion {id: $suffix})
    OPTIONAL MATCH (cb:ClaimBase {id: $suffix})
    RETURN coalesce(fv.base_id, fb.id, cv.base_id, cb.id) AS base_id
    """
    with driver.session() as session:
        r = session.run(query, {"suffix": suffix}).single()
    return r["base_id"] if r else None


# ---------------------------------------------------------------------------
# Fuseki: valor:baseId toevoegen aan een Tessera (idempotent)
# ---------------------------------------------------------------------------

async def _add_base_id_to_tessera(tessera_uri: str, graph_uri: str, base_id: str) -> None:
    import httpx
    from app.services.fuseki import _UPDATE_ENDPOINT, FUSEKI_ADMIN_PASSWORD, _raise_for_fuseki_error

    update = f"""
INSERT {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> <{VALOR_NS}baseId> "{base_id}" .
  }}
}}
WHERE {{
  FILTER NOT EXISTS {{
    GRAPH <{graph_uri}> {{ <{tessera_uri}> <{VALOR_NS}baseId> ?bid }}
  }}
}}
"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _UPDATE_ENDPOINT,
            data={"update": update},
            auth=("admin", FUSEKI_ADMIN_PASSWORD),
            timeout=30,
        )
    _raise_for_fuseki_error(response)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main(dry_run: bool) -> None:
    from app.db.utils import get_driver

    logger.info("=== fix_tessera_base_ids: valor:baseId toevoegen aan bestaande Tesserae ===")
    if dry_run:
        logger.info("DRY-RUN modus — geen schrijfoperaties")

    # Verbinding Neo4j initialiseren
    get_driver()

    # Stap 1: alle Tesserae zonder baseId ophalen
    logger.info("\n[1] Tesserae zonder valor:baseId ophalen uit Fuseki...")
    tesserae = await _get_tesserae_without_base_id()
    logger.info("    Gevonden: %d Tessera(e) zonder valor:baseId", len(tesserae))

    if not tesserae:
        logger.info("Niets te doen — alle Tesserae hebben al een valor:baseId.")
        return

    # Stap 2: base_id oplossen en property toevoegen
    fixed = skipped = errors = 0
    for row in tesserae:
        tessera_uri: str = row["tessera"]
        graph_uri: str = row["graph"]

        # Suffix extraheren uit de Tessera-URI
        if tessera_uri.startswith(TESSERA_PREFIX):
            suffix = tessera_uri[len(TESSERA_PREFIX):]
        else:
            logger.warning("  Onbekende URI-structuur: %s — overgeslagen", tessera_uri)
            skipped += 1
            continue

        # Base_id opzoeken in Neo4j
        base_id = await asyncio.to_thread(_resolve_base_id_neo4j, suffix)

        if not base_id:
            # Suffix is niet gevonden in Neo4j — gebruik suffix zelf als base_id
            # (dit kan een al-correct base_id zijn van een niet-neoJ-gesyncte Tessera)
            logger.warning("  [FALLBACK] %s niet gevonden in Neo4j — suffix als base_id: %s", tessera_uri, suffix)
            base_id = suffix

        if dry_run:
            logger.info("  [DRY-RUN] zou toevoegen: %s → baseId=%s", tessera_uri, base_id)
            fixed += 1
            continue

        try:
            await _add_base_id_to_tessera(tessera_uri, graph_uri, base_id)
            logger.info("  [OK] %s → baseId=%s", tessera_uri, base_id)
            fixed += 1
        except Exception as e:
            logger.error("  [FOUT] %s: %s", tessera_uri, e)
            errors += 1

    logger.info(
        "\n=== Resultaat === %s: gefixeerd=%d, overgeslagen=%d, fouten=%d",
        "DRY-RUN" if dry_run else "UITGEVOERD",
        fixed, skipped, errors,
    )

    if errors > 0:
        logger.error("Er zijn fouten opgetreden. Controleer de output hierboven.")
        sys.exit(1)
    else:
        logger.info("Klaar.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Voeg valor:baseId toe aan bestaande Tesserae")
    parser.add_argument("--dry-run", action="store_true", help="Geen schrijfoperaties")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
