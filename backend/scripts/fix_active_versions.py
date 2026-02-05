import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging

# Ensure we can import from app
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def fix_active_versions_sync():
    logger.info(f"Connecting to Neo4j at {NEO4J_URI}")
    
    query_find_duplicates = """
    MATCH (t:Theme)
    WHERE COUNT { (t)-[:HAS_ACTIVE_VERSION]->() } > 1
    MATCH (t)-[:HAS_ACTIVE_VERSION]->(v:ThemeVersion)
    RETURN t.id as theme_id, t.name as theme_name, collect({id: v.id, created_at: toString(v.created_at), status: v.status}) as versions
    """
    
    with driver.session() as session:
        result = session.run(query_find_duplicates)
        records = list(result)
        
        if not records:
            logger.info("No duplicate active versions found. Database is clean.")
            return

        logger.info(f"Found {len(records)} themes with multiple active versions.")
        
        for record in records:
            theme_id = record["theme_id"]
            versions = record["versions"]
            logger.info(f"Processing Theme {theme_id} ({record['theme_name']}) - {len(versions)} active versions")
            
            # Sort by created_at descending
            versions.sort(key=lambda x: x["created_at"], reverse=True)
            
            latest = versions[0]
            others = versions[1:]
            
            logger.info(f"  Keeping Active: {latest['id']} (Created: {latest['created_at']})")
            
            for old in others:
                logger.info(f"  Fixing: {old['id']} (Created: {old['created_at']})")
                
                fix_query = """
                MATCH (t:Theme {id: $tid})-[r:HAS_ACTIVE_VERSION]->(v:ThemeVersion {id: $vid})
                DELETE r
                SET v.status = 'historical'
                """
                session.run(fix_query, {"tid": theme_id, "vid": old["id"]})
                
    logger.info("Fix complete.")
    driver.close()

if __name__ == "__main__":
    fix_active_versions_sync()
