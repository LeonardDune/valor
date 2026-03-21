"""Migratiescript: synchroniseer actieve Neo4j FactorVersions naar Fuseki.

migrate_themeversions_to_designspaces.py sloeg factor-migratie over voor
DesignSpaces die al bestonden. Dit script repareert dat door alle actieve
FactorVersions alsnog als Tessera naar Fuseki te schrijven.

Gebruik:
    python scripts/migrate_fuseki_sync_factors.py [--dry-run]

Idempotent: bestaande factor-tesserae worden overgeslagen.
"""
import sys
import os
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

DRY_RUN = "--dry-run" in sys.argv

TESSERA_PREFIX = "urn:valor:tessera:"
XSD_NS = "http://www.w3.org/2001/XMLSchema#"


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")


async def main():
    from app.services.fuseki import sparql_select_global, sparql_update
    from app.ontology import VALOR_NS
    from app.db.utils import get_driver

    driver = get_driver()

    # Haal alle actieve FactorVersions op uit Neo4j via ThemeVersion → DesignSpace
    with driver.session() as session:
        results = session.run("""
        MATCH (tv:ThemeVersion)-[:HAS_DESIGN_SPACE]->(ds:DesignSpace)
        MATCH (tv)-[rel:HAS_FACTOR]->(fv:FactorVersion)
        WHERE fv.valid_to IS NULL
        RETURN ds.id AS ds_id,
               fv.id AS fv_id,
               fv.name AS name,
               fv.description AS description,
               coalesce(fv.created_by, '') AS created_by,
               toString(fv.created_at) AS created_at,
               rel.role AS role
        """)
        neo4j_factors = [dict(r) for r in results]

    logger.info(f"Gevonden actieve FactorVersions in Neo4j: {len(neo4j_factors)}")

    if not neo4j_factors:
        # Probeer ook via de nieuwe hiërarchie (Issue → DesignSpace)
        with driver.session() as session:
            results = session.run("""
            MATCH (p:Project)-[:hasIssue]->(:Issue)-[:isAddressedInDesignSpace]->(ds:DesignSpace)
            MATCH (ds)<-[:HAS_DESIGN_SPACE]-(tv:ThemeVersion)
            MATCH (tv)-[rel:HAS_FACTOR]->(fv:FactorVersion)
            WHERE fv.valid_to IS NULL
            RETURN ds.id AS ds_id,
                   fv.id AS fv_id,
                   fv.name AS name,
                   fv.description AS description,
                   coalesce(fv.created_by, '') AS created_by,
                   toString(fv.created_at) AS created_at,
                   rel.role AS role
            """)
            neo4j_factors = [dict(r) for r in results]
        logger.info(f"Via Issue-hiërarchie gevonden: {len(neo4j_factors)}")

    # Groepeer per DesignSpace
    by_ds: dict[str, list] = {}
    for f in neo4j_factors:
        by_ds.setdefault(f["ds_id"], []).append(f)

    total_created = 0
    total_skipped = 0

    for ds_id, factors in by_ds.items():
        asis_graph = f"urn:valor:ds:{ds_id}/asis"
        logger.info(f"DS {ds_id}: {len(factors)} actieve FactorVersions")

        for factor in factors:
            fv_id = factor["fv_id"]
            tessera_uri = f"{TESSERA_PREFIX}{fv_id}"

            # Check of tessera al bestaat in Fuseki
            check = await sparql_select_global(f"""
            SELECT ?baseId WHERE {{
                GRAPH <{asis_graph}> {{
                    <{tessera_uri}> a <{VALOR_NS}Tessera> .
                    OPTIONAL {{ <{tessera_uri}> <{VALOR_NS}baseId> ?baseId }}
                }}
            }}
            """)

            if check:
                logger.info(f"  OK (bestaat al): {fv_id}")
                total_skipped += 1
                continue

            # Tessera bestaat niet — aanmaken
            name = _escape(factor["name"] or "factor")
            role = factor.get("role") or ""
            description = factor.get("description")
            created_by = factor.get("created_by") or ""
            created_at = factor.get("created_at") or "2024-01-01T00:00:00+00:00"

            logger.info(f"  AANMAKEN factor {fv_id}: {factor['name']!r} (role={role})")

            if DRY_RUN:
                total_created += 1
                continue

            role_triple = (
                f'<{tessera_uri}> <{VALOR_NS}factorRole> "{_escape(role)}" .'
                if role else ""
            )
            desc_triple = (
                f'<{tessera_uri}> <{VALOR_NS}description> "{_escape(description)}"@nl .'
                if description else ""
            )
            created_by_triple = (
                f'<{tessera_uri}> <{VALOR_NS}claimedBy> <urn:valor:user:{created_by}> .'
                if created_by else ""
            )

            sparql = f"""
            INSERT DATA {{
                GRAPH <{asis_graph}> {{
                    <{tessera_uri}> a <{VALOR_NS}Tessera> ;
                        <{VALOR_NS}baseId>      "{fv_id}" ;
                        <{VALOR_NS}claimContent> "{name}"@nl ;
                        <{VALOR_NS}claimType>   <{VALOR_NS}AsIsType> ;
                        <{VALOR_NS}epistemicStatus> <{VALOR_NS}ProposedStatus> ;
                        <{VALOR_NS}claimedAt>   "{created_at}"^^<{XSD_NS}dateTime> ;
                        <{VALOR_NS}inDesignSpace> <urn:valor:ds:{ds_id}> .
                    {role_triple}
                    {desc_triple}
                    {created_by_triple}
                }}
            }}
            """
            await sparql_update(sparql, ds_id)
            total_created += 1

    logger.info(f"Klaar: {total_created} aangemaakt, {total_skipped} overgeslagen.")


if __name__ == "__main__":
    if DRY_RUN:
        logger.info("DRY-RUN modus — geen wijzigingen worden doorgevoerd.")
    asyncio.run(main())
