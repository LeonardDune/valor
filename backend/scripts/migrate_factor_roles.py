import os
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env vars - try multiple paths
load_dotenv(dotenv_path="../.env")
if not os.getenv("NEO4J_URI"):
    load_dotenv(dotenv_path="../../.env")
if not os.getenv("NEO4J_URI"):
    # Fallback for when running from project root
    load_dotenv(dotenv_path=".env")

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

def migrate_roles():
    if not NEO4J_URI or not NEO4J_USERNAME or not NEO4J_PASSWORD:
        logger.error("Neo4j credentials not found in env.")
        # Fallback to defaults or exit
        return

    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        driver.verify_connectivity()
        logger.info("Connected to Neo4j.")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        return

    query_migrate = """
    MATCH (th:Theme)-[r:HAS_FACTOR]->(f:Factor)
    WHERE f.type IS NOT NULL
    SET r.role = f.type
    """
    
    query_cleanup = """
    MATCH (f:Factor)
    WHERE f.type IS NOT NULL
    REMOVE f.type
    """
    
    # Optional: Set default role for relationships that might not have one (if any)
    query_default = """
    MATCH (th:Theme)-[r:HAS_FACTOR]->(f:Factor)
    WHERE r.role IS NULL
    SET r.role = 'systeemelement'
    """

    try:
        with driver.session() as session:
            logger.info("Migrating roles from Factor nodes to HAS_FACTOR relationships...")
            result = session.run(query_migrate)
            summary = result.consume()
            logger.info(f"Updated {summary.counters.properties_set} properties in relationships.")

            logger.info("Setting default role for any missing relationships...")
            result = session.run(query_default)
            summary = result.consume()
            logger.info(f"Set default defaults for {summary.counters.properties_set} relationships.")

            logger.info("Removing 'type' property from Factor nodes (Cleanup)...")
            result = session.run(query_cleanup)
            summary = result.consume()
            logger.info(f"Removed type property from {summary.counters.properties_set} nodes.")
            
            logger.info("Migration complete.")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    migrate_roles()
