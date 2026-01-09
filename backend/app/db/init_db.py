import asyncio
import logging
from app.db.utils import get_driver, close_driver

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db():
    driver = get_driver()
    try:
        with open("app/db/schema.cypher", "r") as f:
            schema_cypher = f.read()
        
        statements = [s.strip() for s in schema_cypher.split(";") if s.strip()]
        
        with driver.session() as session:
            for statement in statements:
                logger.info(f"Executing: {statement}")
                session.run(statement)
        
        logger.info("Database initialization completed successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    finally:
        close_driver()

if __name__ == "__main__":
    asyncio.run(init_db())
