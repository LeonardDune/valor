import asyncio
import logging
import os
import sys

# Add parent directory to path to allow imports from app
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.utils import get_driver, verify_connectivity, close_driver

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_space_to_version():
    """
    Migrates Neo4j data from 'Space' terminology to 'ThemeVersion'.
    
    Actions:
    1. Rename Node Label: :Space -> :ThemeVersion
    2. Rename Relationship Type: :HAS_SPACE -> :HAS_VERSION
    """
    logger.info("Starting migration: Space -> ThemeVersion")
    
    try:
        if not await verify_connectivity():
            logger.error("Could not connect to Neo4j. Aborting migration.")
            return

        driver = get_driver()
        
        # 1. Rename Node Labels
        # Find all nodes with :Space, add :ThemeVersion, remove :Space
        logger.info("Step 1: Renaming Node Labels (:Space -> :ThemeVersion)...")
        query_labels = """
        MATCH (n:Space)
        SET n:ThemeVersion
        REMOVE n:Space
        RETURN count(n) as updated_nodes
        """
        with driver.session() as session:
            result = session.run(query_labels)
            count = result.single()["updated_nodes"]
            logger.info(f"Updated {count} nodes from :Space to :ThemeVersion")

        # 2. Rename Relationship Types
        # Find (Theme)-[:HAS_SPACE]->(ThemeVersion) and change to :HAS_VERSION
        # Note: Nodes are already :ThemeVersion now
        logger.info("Step 2: Renaming Relationships (:HAS_SPACE -> :HAS_VERSION)...")
        query_rels = """
        MATCH (t:Theme)-[r:HAS_SPACE]->(v:ThemeVersion)
        CREATE (t)-[new_r:HAS_VERSION]->(v)
        SET new_r = properties(r)
        DELETE r
        RETURN count(new_r) as updated_rels
        """
        with driver.session() as session:
            result = session.run(query_rels)
            count = result.single()["updated_rels"]
            logger.info(f"Updated {count} relationships from :HAS_SPACE to :HAS_VERSION")
            
        logger.info("Migration completed successfully!")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
    finally:
        close_driver()

if __name__ == "__main__":
    asyncio.run(migrate_space_to_version())
