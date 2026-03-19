"""Migratiescript: ThemeVersions → DesignSpaces (US-3.3)

Migreert alle actieve ThemeVersions (inclusief Factors en Claims) naar
DesignSpaces in Neo4j en Fuseki. Het script is idempotent: al gemigreerde
ThemeVersions worden overgeslagen.

Gebruik (vereist draaiende Neo4j + Fuseki):
    cd backend
    FUSEKI_URL=http://localhost:3030 python scripts/migrate_themeversions_to_designspaces.py

    # Dry-run (geen schrijfoperaties):
    FUSEKI_URL=http://localhost:3030 python scripts/migrate_themeversions_to_designspaces.py --dry-run
"""
import asyncio
import sys
import os
import argparse
import logging
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

XSD_NS = "http://www.w3.org/2001/XMLSchema#"


# ---------------------------------------------------------------------------
# Neo4j helpers
# ---------------------------------------------------------------------------

def _get_active_theme_versions(driver) -> list[dict]:
    """Geeft alle actieve ThemeVersions met hun ThemeBase en organisatiehiërarchie."""
    query = """
    MATCH (org:Organization)-[:OWNS]->(p:Project)-[:HAS_THEME]->(t:ThemeBase)
    MATCH (t)-[:HAS_ACTIVE_VERSION|HAS_VERSION]->(v:ThemeVersion)
    WHERE v.valid_to IS NULL
    RETURN
        t.id          AS theme_base_id,
        t.name        AS theme_name,
        t.created_by  AS theme_creator,
        v.id          AS version_id,
        v.name        AS version_name,
        v.description AS version_description,
        toString(v.created_at) AS created_at,
        p.id          AS project_id,
        org.id        AS org_id
    ORDER BY t.id
    """
    with driver.session() as session:
        return [dict(r) for r in session.run(query)]


def _get_factors(driver, version_id: str) -> list[dict]:
    query = """
    MATCH (v:ThemeVersion {id: $vid})-[r:HAS_FACTOR]->(f:FactorVersion)
    WHERE f.valid_to IS NULL
    RETURN
        f.id          AS id,
        f.base_id     AS base_id,
        f.name        AS name,
        coalesce(f.description, '') AS description,
        r.role        AS role,
        toString(f.created_at) AS created_at
    """
    with driver.session() as session:
        return [dict(r) for r in session.run(query, {"vid": version_id})]


def _get_claims(driver, version_id: str) -> list[dict]:
    query = """
    MATCH (v:ThemeVersion {id: $vid})-[:HAS_CLAIM]->(c:ClaimVersion)
    WHERE c.valid_to IS NULL
    RETURN
        c.id                  AS id,
        c.base_id             AS base_id,
        c.statement           AS statement,
        c.polarity            AS polarity,
        c.confidence          AS confidence,
        coalesce(c.evidence_text, '') AS evidence_text,
        coalesce(c.evidence_url, '')  AS evidence_url,
        c.source_version_id   AS source_version_id,
        c.target_version_id   AS target_version_id,
        toString(c.created_at) AS created_at
    """
    with driver.session() as session:
        return [dict(r) for r in session.run(query, {"vid": version_id})]


def _get_or_create_designspace_id(
    driver, theme_version_id: str, name: str, description: Optional[str],
    issue_uri: str, owner_id: str, project_id: str, dry_run: bool
) -> tuple[str, bool]:
    """Geeft (ds_id, already_existed). Maakt aan als nog niet bestaat."""
    check_query = """
    MATCH (ds:DesignSpace {migrated_from_theme_version_id: $vid})
    RETURN ds.id AS id
    """
    with driver.session() as session:
        result = session.run(check_query, {"vid": theme_version_id}).single()
        if result:
            return result["id"], True

    if dry_run:
        import uuid
        return f"dry-run-{uuid.uuid4()}", False

    create_query = """
    MATCH (u:User {id: $uid})
    MATCH (p:Project {id: $pid})
    MATCH (v:ThemeVersion {id: $vid})
    CREATE (ds:DesignSpace {
        id: $id,
        name: $name,
        description: $desc,
        issue_uri: $issue_uri,
        status: 'active',
        created_at: datetime(),
        created_by: $uid,
        migrated_from_theme_version_id: $vid
    })
    CREATE (p)-[:HAS_DESIGN_SPACE]->(ds)
    CREATE (v)-[:HAS_DESIGN_SPACE]->(ds)
    CREATE (u)-[:HAS_ROLE {role: 'admin', created_at: datetime()}]->(ds)
    RETURN ds.id AS id
    """
    import uuid
    ds_id = str(uuid.uuid4())
    with driver.session() as session:
        result = session.run(create_query, {
            "uid": owner_id,
            "pid": project_id,
            "id": ds_id,
            "name": name,
            "desc": description,
            "issue_uri": issue_uri,
            "vid": theme_version_id,
        }).single()
        if not result:
            raise RuntimeError(f"DesignSpace aanmaken mislukt voor ThemeVersion {theme_version_id}")
        return result["id"], False


def _count_fuseki_tesserae(loop, ds_id: str) -> int:
    """Telt het aantal Tesserae in de asis-graph van een DesignSpace."""
    from app.services.fuseki import sparql_select
    asis_graph = f"{ds_id}/asis"
    query = "SELECT (COUNT(?t) AS ?count) WHERE { ?t a <https://valor-ecosystem.nl/ontology/Tessera> }"
    rows = loop.run_until_complete(sparql_select(query, asis_graph))
    return int(rows[0]["count"]) if rows else 0


# ---------------------------------------------------------------------------
# Fuseki helpers
# ---------------------------------------------------------------------------

def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")


async def _insert_tessera_if_absent(
    ds_id: str, tessera_uri: str, content: str,
    creator_uri: str, created_at: str, extra_triples: str = ""
) -> bool:
    """INSERT INTO asis-graph als de Tessera nog niet bestaat. Retourneert True als nieuw."""
    from app.services.fuseki import _SPARQL_ENDPOINT, _UPDATE_ENDPOINT, _raise_for_fuseki_error, FUSEKI_ADMIN_PASSWORD
    import httpx

    VALOR_NS = "https://valor-ecosystem.nl/ontology/"
    asis_graph = f"urn:valor:ds:{ds_id}/asis"
    as_is_uri = f"{VALOR_NS}AsIsType"
    proposed_uri = f"{VALOR_NS}ProposedStatus"

    escaped = _escape(content)
    update = f"""
INSERT {{
  GRAPH <{asis_graph}> {{
    <{tessera_uri}> a <{VALOR_NS}Tessera> ;
      <{VALOR_NS}claimContent> "{escaped}"@nl ;
      <{VALOR_NS}claimType> <{as_is_uri}> ;
      <{VALOR_NS}epistemicStatus> <{proposed_uri}> ;
      <{VALOR_NS}claimedBy> <{creator_uri}> ;
      <{VALOR_NS}claimedAt> "{created_at}"^^<{XSD_NS}dateTime> ;
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


async def migrate_version(
    version: dict, factors: list[dict], claims: list[dict],
    ds_id: str, dry_run: bool
) -> dict:
    """Migreert één ThemeVersion naar een DesignSpace in Fuseki."""
    from app.services.fuseki import initialize_design_space_graphs, sparql_select

    VALOR_NS = "https://valor-ecosystem.nl/ontology/"
    creator = version.get("theme_creator") or "urn:valor:user:unknown"
    creator_uri = f"urn:valor:user:{creator}"

    if not dry_run:
        # Named graphs aanmaken (idempotent via INSERT IF NOT EXISTS)
        await initialize_design_space_graphs(ds_id, f"urn:valor:issue:{version['theme_base_id']}")

    inserted_factors = 0
    inserted_claims = 0

    # Factors → Tesserae
    for f in factors:
        tessera_uri = f"urn:valor:tessera:{f['id']}"
        role_triple = ""
        if f.get("role"):
            role_triple = f'<{tessera_uri}> <{VALOR_NS}factorRole> "{f["role"]}" .'
        if f.get("description"):
            role_triple += f'\n    <{tessera_uri}> <{VALOR_NS}description> "{_escape(f["description"])}"@nl .'

        if not dry_run:
            await _insert_tessera_if_absent(
                ds_id=ds_id,
                tessera_uri=tessera_uri,
                content=f["name"],
                creator_uri=creator_uri,
                created_at=f["created_at"] or version["created_at"],
                extra_triples=role_triple,
            )
        inserted_factors += 1

    # Claims → Tesserae
    for c in claims:
        tessera_uri = f"urn:valor:tessera:{c['id']}"
        source_uri = f"urn:valor:tessera:{c['source_version_id']}"
        target_uri = f"urn:valor:tessera:{c['target_version_id']}"
        extra = f"""
    <{tessera_uri}> <{VALOR_NS}polarity> "{c.get('polarity', 'positive')}" .
    <{tessera_uri}> <{VALOR_NS}confidence> "{c.get('confidence', 0.5)}"^^<{XSD_NS}double> .
    <{tessera_uri}> <{VALOR_NS}fromFactor> <{source_uri}> .
    <{tessera_uri}> <{VALOR_NS}toFactor> <{target_uri}> ."""
        if c.get("evidence_text"):
            extra += f'\n    <{tessera_uri}> <{VALOR_NS}evidenceText> "{_escape(c["evidence_text"])}"@nl .'

        if not dry_run:
            await _insert_tessera_if_absent(
                ds_id=ds_id,
                tessera_uri=tessera_uri,
                content=c["statement"],
                creator_uri=creator_uri,
                created_at=c["created_at"] or version["created_at"],
                extra_triples=extra,
            )
        inserted_claims += 1

    return {"factors": inserted_factors, "claims": inserted_claims}


# ---------------------------------------------------------------------------
# Checksum
# ---------------------------------------------------------------------------

async def verify_checksum(ds_id: str, expected_factors: int, expected_claims: int) -> bool:
    from app.services.fuseki import sparql_select
    VALOR_NS = "https://valor-ecosystem.nl/ontology/"
    asis_graph = f"{ds_id}/asis"

    rows = await sparql_select(
        "SELECT (COUNT(?t) AS ?count) WHERE { ?t a <https://valor-ecosystem.nl/ontology/Tessera> }",
        asis_graph,
    )
    actual = int(rows[0]["count"]) if rows else 0
    expected = expected_factors + expected_claims
    ok = actual == expected
    logger.info(
        "  Checksum: Neo4j=%d (factors=%d claims=%d), Fuseki=%d → %s",
        expected, expected_factors, expected_claims, actual, "OK" if ok else "MISMATCH",
    )
    return ok


# ---------------------------------------------------------------------------
# Repair helpers
# ---------------------------------------------------------------------------

def _ensure_themeversion_designspace_rel(driver, theme_version_id: str, ds_id: str) -> None:
    """Zorg dat ThemeVersion -[:HAS_DESIGN_SPACE]-> DesignSpace bestaat (idempotent)."""
    query = """
    MATCH (v:ThemeVersion {id: $vid})
    MATCH (ds:DesignSpace {id: $dsid})
    MERGE (v)-[:HAS_DESIGN_SPACE]->(ds)
    """
    with driver.session() as session:
        session.run(query, {"vid": theme_version_id, "dsid": ds_id})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main(dry_run: bool):
    from app.db.utils import get_driver

    driver = get_driver()
    versions = _get_active_theme_versions(driver)
    logger.info("Gevonden: %d actieve ThemeVersions", len(versions))

    total_factors = total_claims = skipped = 0
    checksum_failures = []

    for v in versions:
        vid = v["version_id"]
        owner_id = v.get("theme_creator") or ""
        issue_uri = f"urn:valor:issue:{v['theme_base_id']}"

        ds_id, existed = _get_or_create_designspace_id(
            driver=driver,
            theme_version_id=vid,
            name=v["version_name"] or v["theme_name"],
            description=v.get("version_description"),
            issue_uri=issue_uri,
            owner_id=owner_id,
            project_id=v["project_id"],
            dry_run=dry_run,
        )

        if existed:
            skipped += 1
            logger.info("[SKIP] ThemeVersion %s → DesignSpace %s (al gemigreerd)", vid, ds_id)
            if not dry_run:
                _ensure_themeversion_designspace_rel(driver, vid, ds_id)
            continue

        factors = _get_factors(driver, vid)
        claims = _get_claims(driver, vid)

        prefix = "[DRY-RUN]" if dry_run else "[MIGRATE]"
        logger.info(
            "%s ThemeVersion %s → DesignSpace %s | %d factors, %d claims",
            prefix, vid, ds_id, len(factors), len(claims),
        )

        result = await migrate_version(v, factors, claims, ds_id, dry_run)
        total_factors += result["factors"]
        total_claims += result["claims"]

        if not dry_run:
            ok = await verify_checksum(ds_id, len(factors), len(claims))
            if not ok:
                checksum_failures.append(ds_id)

    logger.info(
        "\nResultaat: %d gemigreerd, %d overgeslagen | factors=%d claims=%d",
        len(versions) - skipped, skipped, total_factors, total_claims,
    )
    if checksum_failures:
        logger.error("CHECKSUM MISLUKT voor: %s", checksum_failures)
        sys.exit(1)
    else:
        logger.info("Alle checksums OK.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migreer ThemeVersions naar DesignSpaces")
    parser.add_argument("--dry-run", action="store_true", help="Geen schrijfoperaties")
    args = parser.parse_args()

    if args.dry_run:
        logger.info("DRY-RUN modus — geen wijzigingen worden opgeslagen")

    asyncio.run(main(dry_run=args.dry_run))
