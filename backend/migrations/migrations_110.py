import asyncio
import os
import sys
import logging

# Add backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.db.utils import get_driver

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_migration():
    driver = get_driver()
    logger.info("--- Starting Migration for Story #110: Proposal Lifecycle ---")
    
    # 1. Migrate Factors and Claims to have default status 'accepted'
    # We also touch Organization/Project/Theme to ensure they have the field if we decided to unify later,
    # but for now we focus on Factor/Claim as per domain.py changes.
    # Actually, we can set it on ALL nodes just to be safe and consistent for the 'Proposal' concept.
    
    query_factors = """
    MATCH (f:Factor)
    WHERE f.status IS NULL
    SET f.status = 'accepted'
    RETURN count(f) as count
    """
    
    query_claims = """
    MATCH (c:Claim)
    WHERE c.status IS NULL
    SET c.status = 'accepted'
    RETURN count(c) as count
    """
    
    try:
        with driver.session() as session:
            result_f = session.run(query_factors)
            count_f = result_f.single()["count"]
            logger.info(f"Updated {count_f} Factors to status='accepted'")
            
            result_c = session.run(query_claims)
            count_c = result_c.single()["count"]
            logger.info(f"Updated {count_c} Claims to status='accepted'")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise e

    logger.info("--- Migration #110 Complete ---")

if __name__ == "__main__":
    asyncio.run(run_migration())
