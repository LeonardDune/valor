import os
from neo4j import GraphDatabase, Driver
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

_driver = None

def get_driver() -> Driver:
    global _driver
    if _driver is None:
        if not NEO4J_URI or not NEO4J_USERNAME or not NEO4J_PASSWORD:
            raise ValueError("Neo4j environment variables not set")
        
        try:
            _driver = GraphDatabase.driver(
                NEO4J_URI, 
                auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
            )
            logger.info("Neo4j driver initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j driver: {e}")
            raise e
    return _driver

def close_driver():
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
        logger.info("Neo4j driver closed")

async def verify_connectivity():
    driver = get_driver()
    try:
        driver.verify_connectivity()
        logger.info("Successfully connected to Neo4j AuraDB")
        return True
    except Exception as e:
        logger.error(f"Could not connect to Neo4j: {e}")
        return False
