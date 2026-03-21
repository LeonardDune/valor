"""Migratiescript: synchroniseer actieve Neo4j ClaimVersions naar Fuseki.

Het oude dual-write adapter heeft claims ofwel niet geschreven naar Fuseki,
ofwel met kapotte fromFactor/toFactor verwijzingen (urn:valor:tessera:None).

Dit script:
1. Vindt alle actieve ClaimVersions in Neo4j per DesignSpace
2. Schrijft ontbrekende claims als Tessera naar Fuseki
3. Repareert bestaande claims met gebroken fromFactor/toFactor

Gebruik:
    python scripts/migrate_fuseki_sync_claims.py [--dry-run]

Idempotent: bestaande correcte claim-tesserae worden overgeslagen.
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
NONE_URI = f"{TESSERA_PREFIX}None"


async def main():
    from app.services.fuseki import sparql_select_global, sparql_update
    from app.ontology import VALOR_NS
    from app.db.utils import get_driver

    driver = get_driver()

    # Haal alle actieve claims op uit Neo4j
    neo4j_claims = []
    with driver.session() as session:
        results = session.run("""
        MATCH (tv:ThemeVersion)-[:HAS_DESIGN_SPACE]->(ds:DesignSpace)
        WHERE tv.valid_to IS NULL
        MATCH (tv)-[:HAS_FACTOR]->(srcFV:FactorVersion)-[:CLAIMS]->(cv:ClaimVersion)-[:TO]->(tgtFV:FactorVersion)
        WHERE cv.valid_to IS NULL
        RETURN ds.id AS ds_id,
               cv.id AS cv_id,
               cv.statement AS statement,
               coalesce(cv.polarity, '+') AS polarity,
               coalesce(cv.confidence, 0.8) AS confidence,
               cv.evidence_text AS evidence_text,
               cv.created_by AS created_by,
               srcFV.id AS src_id,
               tgtFV.id AS tgt_id
        """)
        neo4j_claims = [dict(r) for r in results]

    logger.info(f"Gevonden actieve claims in Neo4j: {len(neo4j_claims)}")

    # Groepeer per DesignSpace
    by_ds: dict[str, list] = {}
    for c in neo4j_claims:
        by_ds.setdefault(c["ds_id"], []).append(c)

    total_created = 0
    total_repaired = 0
    total_skipped = 0

    for ds_id, claims in by_ds.items():
        asis_graph = f"urn:valor:ds:{ds_id}/asis"
        logger.info(f"DS {ds_id}: {len(claims)} actieve claims")

        for claim in claims:
            cv_id = claim["cv_id"]
            tessera_uri = f"{TESSERA_PREFIX}{cv_id}"
            src_uri = f"{TESSERA_PREFIX}{claim['src_id']}"
            tgt_uri = f"{TESSERA_PREFIX}{claim['tgt_id']}"

            # Check of tessera al bestaat in Fuseki
            check = await sparql_select_global(f"""
            SELECT ?fromFactor ?toFactor WHERE {{
                GRAPH <{asis_graph}> {{
                    <{tessera_uri}> a <{VALOR_NS}Tessera> .
                    OPTIONAL {{ <{tessera_uri}> <{VALOR_NS}fromFactor> ?fromFactor }}
                    OPTIONAL {{ <{tessera_uri}> <{VALOR_NS}toFactor>   ?toFactor }}
                }}
            }}
            """)

            if check:
                existing_from = check[0].get("fromFactor", "")
                existing_to = check[0].get("toFactor", "")

                if existing_from == NONE_URI or existing_to == NONE_URI:
                    # Repareer kapotte verwijzingen
                    logger.info(f"  REPAREER claim {cv_id}: {existing_from} -> {existing_to}")
                    if not DRY_RUN:
                        repair = f"""
                        DELETE {{
                            GRAPH <{asis_graph}> {{
                                <{tessera_uri}> <{VALOR_NS}fromFactor> ?oldFrom .
                                <{tessera_uri}> <{VALOR_NS}toFactor>   ?oldTo .
                            }}
                        }}
                        INSERT {{
                            GRAPH <{asis_graph}> {{
                                <{tessera_uri}> <{VALOR_NS}fromFactor> <{src_uri}> .
                                <{tessera_uri}> <{VALOR_NS}toFactor>   <{tgt_uri}> .
                            }}
                        }}
                        WHERE {{
                            GRAPH <{asis_graph}> {{
                                OPTIONAL {{ <{tessera_uri}> <{VALOR_NS}fromFactor> ?oldFrom }}
                                OPTIONAL {{ <{tessera_uri}> <{VALOR_NS}toFactor>   ?oldTo }}
                            }}
                        }}
                        """
                        await sparql_update(repair, ds_id)
                    total_repaired += 1
                else:
                    logger.info(f"  OK (al correct): {cv_id}")
                    total_skipped += 1
                continue

            # Tessera bestaat niet — aanmaken
            stmt = claim["statement"] or "invloed"
            polarity = claim["polarity"] or "+"
            confidence = float(claim["confidence"]) if claim["confidence"] else 0.8
            evidence = claim.get("evidence_text")
            created_by = claim.get("created_by") or ""

            logger.info(f"  AANMAKEN claim {cv_id}: {claim['src_id']} -> {claim['tgt_id']}")

            if DRY_RUN:
                total_created += 1
                continue

            evidence_triple = (
                f'<{tessera_uri}> <{VALOR_NS}evidenceText> "{evidence}" .'
                if evidence else ""
            )
            created_by_triple = (
                f'<{tessera_uri}> <{VALOR_NS}claimedBy> <urn:valor:user:{created_by}> .'
                if created_by else ""
            )

            sparql = f"""
            INSERT DATA {{
                GRAPH <{asis_graph}> {{
                    <{tessera_uri}> a <{VALOR_NS}Tessera> ;
                        <{VALOR_NS}baseId>      "{cv_id}" ;
                        <{VALOR_NS}claimContent> "{stmt}" ;
                        <{VALOR_NS}fromFactor>  <{src_uri}> ;
                        <{VALOR_NS}toFactor>    <{tgt_uri}> ;
                        <{VALOR_NS}polarity>    "{polarity}" ;
                        <{VALOR_NS}confidence>  {confidence} ;
                        <{VALOR_NS}claimType>   <{VALOR_NS}AsIsType> ;
                        <{VALOR_NS}epistemicStatus> <{VALOR_NS}ProposedStatus> ;
                        <{VALOR_NS}inDesignSpace> <urn:valor:ds:{ds_id}> .
                    {evidence_triple}
                    {created_by_triple}
                }}
            }}
            """
            await sparql_update(sparql, ds_id)
            total_created += 1

    logger.info(f"Klaar: {total_created} aangemaakt, {total_repaired} gerepareerd, {total_skipped} overgeslagen.")


if __name__ == "__main__":
    if DRY_RUN:
        logger.info("DRY-RUN modus — geen wijzigingen worden doorgevoerd.")
    asyncio.run(main())
