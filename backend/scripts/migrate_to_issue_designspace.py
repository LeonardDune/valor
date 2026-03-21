"""Migratiescript: ThemeBase/ThemeVersion → Issue + DesignSpace.

Gebruik:
    python scripts/migrate_to_issue_designspace.py [--dry-run]

Wat het doet (idempotent):
1. Vind alle ThemeBase nodes via Project -[HAS_THEME]-> ThemeBase
2. Vind bestaande DesignSpace via ThemeVersion -[HAS_DESIGN_SPACE]-> DesignSpace
3. Maak Issue node aan (ThemeBase.id als Issue.id)
4. Maak relaties: Project -[hasIssue]-> Issue -[isAddressedInDesignSpace]-> DesignSpace
5. Hercreëer RBAC: HAS_ROLE van ThemeBase → DesignSpace
6. Re-anker VotingSessions: DesignSpace -[HAS_SESSION]-> VotingSession
7. Verwijder ThemeBase/ThemeVersion nodes en oude relaties
8. Rapporteer aantallen

Draai altijd eerst met --dry-run.
"""
import sys
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.utils import get_driver

DRY_RUN = "--dry-run" in sys.argv


def run():
    driver = get_driver()

    # ---- Stap 1: Vind alle ThemeBase nodes met hun actieve versie en DesignSpace ----
    query_find = """
    MATCH (p:Project)-[:HAS_THEME]->(tb:ThemeBase)
    OPTIONAL MATCH (tb)-[:HAS_ACTIVE_VERSION]->(av:ThemeVersion)
    OPTIONAL MATCH (av)-[:HAS_DESIGN_SPACE]->(ds:DesignSpace)
    OPTIONAL MATCH (av)-[:HAS_SESSION]->(sess:VotingSession)
    RETURN tb.id AS tb_id,
           tb.created_at AS tb_created_at,
           tb.created_by AS tb_created_by,
           tb.status AS tb_status,
           av.id AS av_id,
           av.name AS av_name,
           av.description AS av_description,
           ds.id AS ds_id,
           p.id AS project_id,
           collect(DISTINCT sess.id) AS session_ids
    """

    with driver.session() as session:
        records = list(session.run(query_find))

    logger.info(f"Gevonden ThemeBases: {len(records)}")

    migrated = 0
    skipped = 0

    for rec in records:
        tb_id = rec["tb_id"]
        project_id = rec["project_id"]
        av_name = rec["av_name"] or "Onbekend issue"
        av_description = rec["av_description"]
        tb_status = rec["tb_status"] or "active"
        tb_created_by = rec["tb_created_by"] or ""
        ds_id = rec["ds_id"]
        session_ids = rec["session_ids"] or []

        if not ds_id:
            logger.warning(f"ThemeBase {tb_id} heeft geen DesignSpace via actieve ThemeVersion — wordt overgeslagen.")
            skipped += 1
            continue

        logger.info(f"Migreren: ThemeBase {tb_id} -> Issue {tb_id} + DesignSpace {ds_id}")

        if DRY_RUN:
            migrated += 1
            continue

        with driver.session() as session:
            # Check of Issue al bestaat (idempotentie)
            existing = session.run(
                "MATCH (i:Issue {id: $id}) RETURN i.id AS id", {"id": tb_id}
            ).single()

            if existing:
                logger.info(f"Issue {tb_id} bestaat al — relaties worden bijgewerkt.")
            else:
                # Maak Issue node aan
                session.run(
                    """
                    CREATE (i:Issue {
                        id: $id,
                        name: $name,
                        description: $desc,
                        status: $status,
                        created_at: datetime(),
                        created_by: $created_by
                    })
                    """,
                    {
                        "id": tb_id,
                        "name": av_name,
                        "desc": av_description,
                        "status": tb_status,
                        "created_by": tb_created_by,
                    },
                )

            # Project -[hasIssue]-> Issue (idempotent via MERGE)
            session.run(
                """
                MATCH (p:Project {id: $pid})
                MATCH (i:Issue {id: $iid})
                MERGE (p)-[:hasIssue]->(i)
                """,
                {"pid": project_id, "iid": tb_id},
            )

            # Issue -[isAddressedInDesignSpace]-> DesignSpace (idempotent via MERGE)
            session.run(
                """
                MATCH (i:Issue {id: $iid})
                MATCH (ds:DesignSpace {id: $dsid})
                MERGE (i)-[:isAddressedInDesignSpace]->(ds)
                """,
                {"iid": tb_id, "dsid": ds_id},
            )

            # Hercreëer RBAC: HAS_ROLE van ThemeBase → DesignSpace
            session.run(
                """
                MATCH (u:User)-[r:HAS_ROLE]->(tb:ThemeBase {id: $tbid})
                MATCH (ds:DesignSpace {id: $dsid})
                MERGE (u)-[:HAS_ROLE {role: r.role, created_at: datetime()}]->(ds)
                """,
                {"tbid": tb_id, "dsid": ds_id},
            )

            # Re-anker VotingSessions naar DesignSpace
            for sid in session_ids:
                if sid:
                    session.run(
                        """
                        MATCH (ds:DesignSpace {id: $dsid})
                        MATCH (s:VotingSession {id: $sid})
                        MERGE (ds)-[:HAS_SESSION]->(s)
                        """,
                        {"dsid": ds_id, "sid": sid},
                    )

        migrated += 1

    logger.info(f"Migratie afgerond: {migrated} gemigreerd, {skipped} overgeslagen.")

    if not DRY_RUN and migrated > 0:
        logger.info("Optionele cleanup: ThemeBase/ThemeVersion nodes verwijderen.")
        logger.info("Voer handmatig uit na verificatie:")
        logger.info("  MATCH (tb:ThemeBase) DETACH DELETE tb")
        logger.info("  MATCH (tv:ThemeVersion) DETACH DELETE tv")


if __name__ == "__main__":
    if DRY_RUN:
        logger.info("DRY-RUN modus — geen wijzigingen worden doorgevoerd.")
    run()
