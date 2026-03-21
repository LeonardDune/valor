"""Herbouw de asis-graph in Fuseki volledig vanuit Neo4j.

Wist de bestaande asis-graph per DesignSpace en schrijft alle actieve
FactorVersions en ClaimVersions vers als Tesserae.

Gebruik:
    python scripts/migrate_fuseki_rebuild_asis.py [--dry-run]
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

    # Haal alle DesignSpaces op met hun ThemeVersion
    with driver.session() as session:
        ds_rows = list(session.run("""
        MATCH (tv:ThemeVersion)-[:HAS_DESIGN_SPACE]->(ds:DesignSpace)
        RETURN DISTINCT ds.id AS ds_id, tv.id AS tv_id
        """))

    logger.info(f"Gevonden DesignSpaces: {len(ds_rows)}")

    for row in ds_rows:
        ds_id = row["ds_id"]
        tv_id = row["tv_id"]
        asis_graph = f"urn:valor:ds:{ds_id}/asis"

        logger.info(f"DS {ds_id}: asis-graph wissen en herbouwen")

        if not DRY_RUN:
            await sparql_update(f"CLEAR GRAPH <{asis_graph}>", ds_id)

        # Haal factoren op voor deze ThemeVersion
        with driver.session() as session:
            factor_rows = list(session.run("""
            MATCH (tv:ThemeVersion {id: $tv_id})-[rel:HAS_FACTOR]->(fv:FactorVersion)
            WHERE fv.valid_to IS NULL
            RETURN fv.id AS fv_id,
                   fv.name AS name,
                   fv.description AS description,
                   coalesce(fv.created_by, '') AS created_by,
                   toString(fv.created_at) AS created_at,
                   rel.role AS role
            """, {"tv_id": tv_id}))

        logger.info(f"  Factoren: {len(factor_rows)}")

        for f in factor_rows:
            fv_id = f["fv_id"]
            tessera_uri = f"{TESSERA_PREFIX}{fv_id}"
            name = _escape(f["name"] or "factor")
            role = f["role"] or ""
            description = f.get("description")
            created_by = f.get("created_by") or ""
            created_at = f.get("created_at") or "2024-01-01T00:00:00+00:00"

            role_triple = f'<{tessera_uri}> <{VALOR_NS}factorRole> "{_escape(role)}" .' if role else ""
            desc_triple = f'<{tessera_uri}> <{VALOR_NS}description> "{_escape(description)}"@nl .' if description else ""
            created_by_triple = f'<{tessera_uri}> <{VALOR_NS}claimedBy> <urn:valor:user:{created_by}> .' if created_by else ""

            if not DRY_RUN:
                await sparql_update(f"""
                INSERT DATA {{
                    GRAPH <{asis_graph}> {{
                        <{tessera_uri}> a <{VALOR_NS}Tessera> ;
                            <{VALOR_NS}baseId>       "{fv_id}" ;
                            <{VALOR_NS}claimContent>  "{name}"@nl ;
                            <{VALOR_NS}claimType>    <{VALOR_NS}AsIsType> ;
                            <{VALOR_NS}epistemicStatus> <{VALOR_NS}ProposedStatus> ;
                            <{VALOR_NS}claimedAt>    "{created_at}"^^<{XSD_NS}dateTime> ;
                            <{VALOR_NS}inDesignSpace> <urn:valor:ds:{ds_id}> .
                        {role_triple}
                        {desc_triple}
                        {created_by_triple}
                    }}
                }}
                """, ds_id)

        # Haal claims op voor deze ThemeVersion
        with driver.session() as session:
            claim_rows = list(session.run("""
            MATCH (tv:ThemeVersion {id: $tv_id})-[:HAS_FACTOR]->(srcFV:FactorVersion)
                  -[:CLAIMS]->(cv:ClaimVersion)-[:TO]->(tgtFV:FactorVersion)
            WHERE cv.valid_to IS NULL
            RETURN cv.id AS cv_id,
                   cv.statement AS statement,
                   coalesce(cv.polarity, '+') AS polarity,
                   coalesce(cv.confidence, 0.8) AS confidence,
                   cv.evidence_text AS evidence_text,
                   cv.created_by AS created_by,
                   srcFV.id AS src_id,
                   tgtFV.id AS tgt_id
            """, {"tv_id": tv_id}))

        logger.info(f"  Claims: {len(claim_rows)}")

        for c in claim_rows:
            cv_id = c["cv_id"]
            tessera_uri = f"{TESSERA_PREFIX}{cv_id}"
            src_uri = f"{TESSERA_PREFIX}{c['src_id']}"
            tgt_uri = f"{TESSERA_PREFIX}{c['tgt_id']}"
            stmt = _escape(c["statement"] or "invloed")
            polarity = c["polarity"] or "+"
            confidence = float(c["confidence"]) if c["confidence"] else 0.8
            evidence = c.get("evidence_text")
            created_by = c.get("created_by") or ""

            evidence_triple = f'<{tessera_uri}> <{VALOR_NS}evidenceText> "{_escape(evidence)}" .' if evidence else ""
            created_by_triple = f'<{tessera_uri}> <{VALOR_NS}claimedBy> <urn:valor:user:{created_by}> .' if created_by else ""

            if not DRY_RUN:
                await sparql_update(f"""
                INSERT DATA {{
                    GRAPH <{asis_graph}> {{
                        <{tessera_uri}> a <{VALOR_NS}Tessera> ;
                            <{VALOR_NS}baseId>       "{cv_id}" ;
                            <{VALOR_NS}claimContent>  "{stmt}" ;
                            <{VALOR_NS}fromFactor>   <{src_uri}> ;
                            <{VALOR_NS}toFactor>     <{tgt_uri}> ;
                            <{VALOR_NS}polarity>     "{polarity}" ;
                            <{VALOR_NS}confidence>   {confidence} ;
                            <{VALOR_NS}claimType>    <{VALOR_NS}AsIsType> ;
                            <{VALOR_NS}epistemicStatus> <{VALOR_NS}ProposedStatus> ;
                            <{VALOR_NS}inDesignSpace> <urn:valor:ds:{ds_id}> .
                        {evidence_triple}
                        {created_by_triple}
                    }}
                }}
                """, ds_id)

        logger.info(f"  DS {ds_id}: klaar ({len(factor_rows)} factoren, {len(claim_rows)} claims)")

    logger.info("Herbouw compleet.")


if __name__ == "__main__":
    if DRY_RUN:
        logger.info("DRY-RUN modus — geen wijzigingen worden doorgevoerd.")
    asyncio.run(main())
