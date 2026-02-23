import os
import uuid
import logging
from datetime import datetime
from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j connection details from environment
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://causa-neo4j:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")

def migrate_factor_roles(dry_run=False):
    """
    Migrates the 'type' property from FactorVersion nodes to the 'role' property
    on the incoming HAS_FACTOR relationship from ThemeVersion.
    """
    if dry_run:
        logger.info("[DRY RUN] Starting migration: FactorVersion.type -> HAS_FACTOR.role")
    else:
        logger.info("Starting migration: FactorVersion.type -> HAS_FACTOR.role")
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        # 1. Find all relationships to migrate
        query_find = """
        MATCH (tv:ThemeVersion)-[r:HAS_FACTOR]->(fv:FactorVersion)
        WHERE fv.type IS NOT NULL
        RETURN tv.id as theme_version_id, fv.id as factor_version_id, fv.type as factor_type, r.role as existing_role
        """
        
        results = session.run(query_find)
        records = list(results)
        logger.info(f"Found {len(records)} relationships to potentially migrate.")
        
        # 2. Apply migration in a transaction
        query_migrate = """
        MATCH (tv:ThemeVersion)-[r:HAS_FACTOR]->(fv:FactorVersion)
        WHERE fv.type IS NOT NULL
        SET r.role = fv.type
        REMOVE fv.type
        RETURN count(*) as migrated_count
        """
        
        with session.begin_transaction() as tx:
            result = tx.run(query_migrate)
            migrated_count = result.single()["migrated_count"]
            if dry_run:
                tx.rollback()
                logger.info(f"[DRY RUN] Migration preview complete. {migrated_count} relationships WOULD BE updated and properties removed (Transaction Rolled Back).")
            else:
                tx.commit()
                logger.info(f"Migration complete. {migrated_count} relationships updated and properties removed.")

    driver.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Migrate FactorVersion types to roles.")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without committing changes.")
    args = parser.parse_args()

    try:
        migrate_factor_roles(dry_run=args.dry_run)
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        exit(1)
