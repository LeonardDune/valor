"""Verificatie- en repairscript voor US-11.1: Neo4j kennisdata → Fuseki Tesserae.

Controleert of alle actieve Factors en Claims uit Neo4j als valor:Tessera-resources
aanwezig zijn in de Fuseki asis-graph van hun bijbehorende DesignSpace. Rapporteert
checksums per ThemeVersion en schrijft een JSON-migratielogboek.

Gebruik:
    cd backend

    # Alleen verificatie (geen wijzigingen):
    FUSEKI_URL=http://localhost:3030 python scripts/verify_migration_11_1.py

    # Verificatie + repair (voegt ontbrekende Tesserae in):
    FUSEKI_URL=http://localhost:3030 python scripts/verify_migration_11_1.py --repair

    # Dry-run (geen schrijfoperaties, wel volledige rapportage):
    FUSEKI_URL=http://localhost:3030 python scripts/verify_migration_11_1.py --dry-run
"""
import asyncio
import sys
import os
import argparse
import json
import logging
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

VALOR_NS = "https://valor-ecosystem.nl/ontology/"
XSD_NS = "http://www.w3.org/2001/XMLSchema#"


# ---------------------------------------------------------------------------
# Neo4j helpers
# ---------------------------------------------------------------------------

def _get_themeversions_with_designspaces(driver) -> list[dict]:
    """Geeft alle actieve ThemeVersions met hun gekoppelde DesignSpace (indien aanwezig)."""
    query = """
    MATCH (org:Organization)-[:OWNS]->(p:Project)-[:HAS_THEME]->(t:ThemeBase)
    MATCH (t)-[:HAS_VERSION]->(v:ThemeVersion)
    WHERE v.valid_to IS NULL
    OPTIONAL MATCH (v)-[:HAS_DESIGN_SPACE]->(ds:DesignSpace)
    RETURN
        v.id          AS version_id,
        v.name        AS version_name,
        t.id          AS theme_base_id,
        t.name        AS theme_name,
        t.created_by  AS theme_creator,
        ds.id         AS ds_id
    ORDER BY v.id
    """
    with driver.session() as session:
        return [dict(r) for r in session.run(query)]


def _count_neo4j_factors(driver, version_id: str) -> int:
    query = """
    MATCH (v:ThemeVersion {id: $vid})-[:HAS_FACTOR]->(f:FactorVersion)
    WHERE f.valid_to IS NULL
    RETURN COUNT(f) AS cnt
    """
    with driver.session() as session:
        result = session.run(query, {"vid": version_id}).single()
        return result["cnt"] if result else 0


def _get_neo4j_factors(driver, version_id: str) -> list[dict]:
    query = """
    MATCH (v:ThemeVersion {id: $vid})-[r:HAS_FACTOR]->(f:FactorVersion)
    WHERE f.valid_to IS NULL
    RETURN
        f.id          AS id,
        f.name        AS name,
        coalesce(f.description, '') AS description,
        r.role        AS role,
        toString(f.created_at) AS created_at
    """
    with driver.session() as session:
        return [dict(r) for r in session.run(query, {"vid": version_id})]


def _count_neo4j_claims(driver, version_id: str) -> int:
    query = """
    MATCH (v:ThemeVersion {id: $vid})-[:HAS_CLAIM]->(c:ClaimVersion)
    WHERE c.valid_to IS NULL
    RETURN COUNT(c) AS cnt
    """
    with driver.session() as session:
        result = session.run(query, {"vid": version_id}).single()
        return result["cnt"] if result else 0


def _get_neo4j_claims(driver, version_id: str) -> list[dict]:
    query = """
    MATCH (v:ThemeVersion {id: $vid})-[:HAS_CLAIM]->(c:ClaimVersion)
    WHERE c.valid_to IS NULL
    RETURN
        c.id                  AS id,
        c.statement           AS statement,
        c.polarity            AS polarity,
        coalesce(c.confidence, 0.5) AS confidence,
        coalesce(c.evidence_text, '') AS evidence_text,
        c.source_version_id   AS source_version_id,
        c.target_version_id   AS target_version_id,
        toString(c.created_at) AS created_at
    """
    with driver.session() as session:
        return [dict(r) for r in session.run(query, {"vid": version_id})]


def _check_neo4j_users_intact(driver) -> bool:
    """Controleert dat User/Organization/HAS_ROLE nodes ongewijzigd zijn in Neo4j."""
    query = """
    MATCH (u:User)
    RETURN COUNT(u) AS users
    """
    with driver.session() as session:
        result = session.run(query).single()
        count = result["users"] if result else 0
    logger.info("  Neo4j gebruikers: %d (ongewijzigd aanwezig)", count)
    return count > 0


# ---------------------------------------------------------------------------
# Fuseki helpers
# ---------------------------------------------------------------------------

async def _count_fuseki_tesserae(ds_id: str) -> int:
    """Telt alle valor:Tessera resources in de asis-graph van een DesignSpace."""
    from app.services.fuseki import sparql_select
    asis_graph = f"{ds_id}/asis"
    rows = await sparql_select(
        f"SELECT (COUNT(?t) AS ?count) WHERE {{ ?t a <{VALOR_NS}Tessera> }}",
        asis_graph,
    )
    return int(rows[0]["count"]) if rows else 0


async def _get_fuseki_tessera_uris(ds_id: str) -> set[str]:
    """Geeft alle Tessera-URIs in de asis-graph van een DesignSpace."""
    from app.services.fuseki import sparql_select
    asis_graph = f"{ds_id}/asis"
    rows = await sparql_select(
        f"SELECT ?t WHERE {{ ?t a <{VALOR_NS}Tessera> }}",
        asis_graph,
    )
    return {row["t"] for row in rows}


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")


async def _insert_tessera_if_absent(
    ds_id: str,
    tessera_uri: str,
    content: str,
    creator_uri: str,
    created_at: str,
    extra_triples: str = "",
) -> bool:
    """Voegt een Tessera in de asis-graph in, alleen als die nog niet bestaat."""
    import httpx
    from app.services.fuseki import _UPDATE_ENDPOINT, FUSEKI_ADMIN_PASSWORD, _raise_for_fuseki_error

    asis_graph = f"urn:valor:ds:{ds_id}/asis"
    proposed_uri = f"{VALOR_NS}ProposedStatus"
    as_is_uri = f"{VALOR_NS}AsIsType"
    escaped = _escape(content)
    ts = created_at or datetime.now(timezone.utc).isoformat()

    update = f"""
INSERT {{
  GRAPH <{asis_graph}> {{
    <{tessera_uri}> a <{VALOR_NS}Tessera> ;
      <{VALOR_NS}claimContent> "{escaped}"@nl ;
      <{VALOR_NS}claimType> <{as_is_uri}> ;
      <{VALOR_NS}epistemicStatus> <{proposed_uri}> ;
      <{VALOR_NS}claimedBy> <{creator_uri}> ;
      <{VALOR_NS}claimedAt> "{ts}"^^<{XSD_NS}dateTime> ;
      <{VALOR_NS}inDesignSpace> <urn:valor:ds:{ds_id}> .
    {extra_triples}
  }}
}}
WHERE {{
  FILTER NOT EXISTS {{
    GRAPH <{asis_graph}> {{ <{tessera_uri}> a <{VALOR_NS}Tessera> }}
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
    return True


# ---------------------------------------------------------------------------
# Verificatie per DesignSpace
# ---------------------------------------------------------------------------

async def verify_design_space(
    version: dict,
    driver,
    repair: bool,
    dry_run: bool,
) -> dict:
    """Verificeert één ThemeVersion/DesignSpace en rapporteert het resultaat."""
    vid = version["version_id"]
    ds_id = version["ds_id"]
    creator = version.get("theme_creator") or "unknown"
    creator_uri = f"urn:valor:user:{creator}"

    result: dict = {
        "version_id": vid,
        "version_name": version.get("version_name") or version.get("theme_name"),
        "ds_id": ds_id,
        "neo4j_factors": 0,
        "neo4j_claims": 0,
        "fuseki_tesserae": 0,
        "missing_factors": [],
        "missing_claims": [],
        "checksum_ok": False,
        "repaired_factors": 0,
        "repaired_claims": 0,
        "status": "ok",
    }

    if not ds_id:
        result["status"] = "no_designspace"
        logger.warning("  [SKIP] ThemeVersion %s heeft geen DesignSpace — niet gemigreerd", vid)
        return result

    # Neo4j aantallen
    factors = _get_neo4j_factors(driver, vid)
    claims = _get_neo4j_claims(driver, vid)
    result["neo4j_factors"] = len(factors)
    result["neo4j_claims"] = len(claims)

    # Fuseki aantallen + aanwezige URIs
    fuseki_count = await _count_fuseki_tesserae(ds_id)
    present_uris = await _get_fuseki_tessera_uris(ds_id)
    result["fuseki_tesserae"] = fuseki_count

    # Vergelijk per resource
    missing_factors = [f for f in factors if f"urn:valor:tessera:{f['id']}" not in present_uris]
    missing_claims = [c for c in claims if f"urn:valor:tessera:{c['id']}" not in present_uris]
    result["missing_factors"] = [f["id"] for f in missing_factors]
    result["missing_claims"] = [c["id"] for c in missing_claims]

    expected = len(factors) + len(claims)
    result["checksum_ok"] = fuseki_count >= expected and not missing_factors and not missing_claims

    if result["checksum_ok"]:
        logger.info(
            "  [OK]  DesignSpace %s | neo4j=%d+%d fuseki=%d",
            ds_id, len(factors), len(claims), fuseki_count,
        )
        return result

    logger.warning(
        "  [MISMATCH] DesignSpace %s | neo4j=%d+%d fuseki=%d | ontbreekt: %d factors, %d claims",
        ds_id, len(factors), len(claims), fuseki_count,
        len(missing_factors), len(missing_claims),
    )
    result["status"] = "mismatch"

    if not repair or dry_run:
        return result

    # Repair: voeg ontbrekende factors in
    for f in missing_factors:
        tessera_uri = f"urn:valor:tessera:{f['id']}"
        extra = ""
        if f.get("role"):
            extra += f'<{tessera_uri}> <{VALOR_NS}factorRole> "{_escape(f["role"])}" .\n'
        if f.get("description"):
            extra += f'<{tessera_uri}> <{VALOR_NS}description> "{_escape(f["description"])}"@nl .\n'
        await _insert_tessera_if_absent(
            ds_id=ds_id,
            tessera_uri=tessera_uri,
            content=f["name"],
            creator_uri=creator_uri,
            created_at=f["created_at"],
            extra_triples=extra,
        )
        result["repaired_factors"] += 1
        logger.info("    REPAIR factor %s → %s", f["id"], tessera_uri)

    # Repair: voeg ontbrekende claims in
    for c in missing_claims:
        tessera_uri = f"urn:valor:tessera:{c['id']}"
        source_uri = f"urn:valor:tessera:{c['source_version_id']}"
        target_uri = f"urn:valor:tessera:{c['target_version_id']}"
        extra = f"""<{tessera_uri}> <{VALOR_NS}polarity> "{_escape(str(c.get('polarity', '+')))}\" .
    <{tessera_uri}> <{VALOR_NS}confidence> "{c.get('confidence', 0.5)}"^^<{XSD_NS}double> .
    <{tessera_uri}> <{VALOR_NS}fromFactor> <{source_uri}> .
    <{tessera_uri}> <{VALOR_NS}toFactor> <{target_uri}> ."""
        if c.get("evidence_text"):
            extra += f'\n    <{tessera_uri}> <{VALOR_NS}evidenceText> "{_escape(c["evidence_text"])}"@nl .'
        await _insert_tessera_if_absent(
            ds_id=ds_id,
            tessera_uri=tessera_uri,
            content=c["statement"],
            creator_uri=creator_uri,
            created_at=c["created_at"],
            extra_triples=extra,
        )
        result["repaired_claims"] += 1
        logger.info("    REPAIR claim %s → %s", c["id"], tessera_uri)

    # Hercontrole na repair
    fuseki_count_after = await _count_fuseki_tesserae(ds_id)
    result["fuseki_tesserae"] = fuseki_count_after
    result["checksum_ok"] = fuseki_count_after >= expected
    result["status"] = "repaired" if result["checksum_ok"] else "repair_failed"
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main(repair: bool, dry_run: bool, report_path: str) -> None:
    from app.db.utils import get_driver

    driver = get_driver()

    logger.info("=== US-11.1 Migratieverificatie: Neo4j → Fuseki Tesserae ===")
    if dry_run:
        logger.info("DRY-RUN modus — geen schrijfoperaties")
    elif repair:
        logger.info("REPAIR modus — ontbrekende Tesserae worden ingevoegd")
    else:
        logger.info("VERIFICATIE modus — read-only")

    # Integriteitscheck Neo4j gebruikers
    logger.info("\n[0] Gebruikersdata Neo4j controleren...")
    _check_neo4j_users_intact(driver)

    # Alle ThemeVersions + DesignSpaces ophalen
    logger.info("\n[1] ThemeVersions + DesignSpaces ophalen...")
    versions = _get_themeversions_with_designspaces(driver)
    logger.info("    Gevonden: %d ThemeVersion(s)", len(versions))

    if not versions:
        logger.warning("Geen ThemeVersions gevonden — is er data in Neo4j?")
        sys.exit(0)

    # Verificatie per DesignSpace
    logger.info("\n[2] Verificatie per DesignSpace...")
    results = []
    for v in versions:
        results.append(await verify_design_space(v, driver, repair=repair, dry_run=dry_run))

    # Samenvatting
    total = len(results)
    ok = sum(1 for r in results if r["status"] == "ok")
    mismatches = sum(1 for r in results if r["status"] == "mismatch")
    repaired = sum(1 for r in results if r["status"] == "repaired")
    no_ds = sum(1 for r in results if r["status"] == "no_designspace")
    repair_failed = sum(1 for r in results if r["status"] == "repair_failed")

    logger.info("\n=== Samenvatting ===")
    logger.info("  Totaal ThemeVersions : %d", total)
    logger.info("  OK (checksum klopt)  : %d", ok)
    logger.info("  Geen DesignSpace     : %d", no_ds)
    logger.info("  Mismatch (niet gerep): %d", mismatches)
    logger.info("  Gerepareerd          : %d", repaired)
    logger.info("  Repair mislukt       : %d", repair_failed)

    # Rapport schrijven
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "dry-run" if dry_run else ("repair" if repair else "verify"),
        "summary": {
            "total": total,
            "ok": ok,
            "no_designspace": no_ds,
            "mismatch": mismatches,
            "repaired": repaired,
            "repair_failed": repair_failed,
        },
        "details": results,
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    logger.info("\nMigratielogboek geschreven: %s", report_path)

    if mismatches > 0 or repair_failed > 0:
        logger.error("VERIFICATIE MISLUKT: er zijn checksumfouten. Gebruik --repair om te herstellen.")
        sys.exit(1)
    else:
        logger.info("Verificatie geslaagd.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verificatie US-11.1: Neo4j → Fuseki Tesserae")
    parser.add_argument("--repair", action="store_true", help="Voeg ontbrekende Tesserae in")
    parser.add_argument("--dry-run", action="store_true", help="Geen schrijfoperaties")
    parser.add_argument(
        "--report",
        default="migration_report_11_1.json",
        help="Pad naar het JSON-migratielogboek (default: migration_report_11_1.json)",
    )
    args = parser.parse_args()

    if args.dry_run and args.repair:
        logger.error("--dry-run en --repair zijn niet combineerbaar")
        sys.exit(1)

    asyncio.run(main(repair=args.repair, dry_run=args.dry_run, report_path=args.report))
