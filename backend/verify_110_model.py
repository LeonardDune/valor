import asyncio
import os
import sys
import logging
import uuid
from datetime import datetime

# Add backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.db.utils import get_driver
from app.models.domain import Proposal, LifecycleStatus, Conflict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_110():
    driver = get_driver()
    test_id = str(uuid.uuid4())[:8]
    logger.info(f"--- Verifying Story #110 (Test ID: {test_id}) ---")

    # 1. Verify Migration (Check database for accepted content)
    # We assume migration has run.
    query_check = """
    MATCH (n) WHERE n:Factor OR n:Claim
    RETURN count(n) as total, sum(CASE WHEN n.status = 'accepted' THEN 1 ELSE 0 END) as accepted_count
    """
    with driver.session() as session:
        result = session.run(query_check)
        record = result.single()
        total = record["total"]
        accepted = record["accepted_count"]
        
        if total > 0 and accepted == total:
             logger.info(f"PASS: All {total} content nodes have status='accepted'.")
        elif total == 0:
             logger.warn("WARN: No content nodes found to verify migration.")
        else:
             logger.error(f"FAIL: Only {accepted}/{total} nodes have status='accepted'.")

    # 2. Verify Proposal Model Instantiation
    try:
        p = Proposal(
            title=f"Test Proposal {test_id}", 
            description="Testing model", 
            author_id=f"user_{test_id}"
        )
        if p.status == LifecycleStatus.DRAFT:
            logger.info("PASS: Proposal model instantiated with default DRAFT status.")
        else:
            logger.error(f"FAIL: Proposal status is {p.status}")
    except Exception as e:
        logger.error(f"FAIL: Could not instantiate Proposal model: {e}")

    # 3. Verify Conflict Model Instantiation
    try:
        c = Conflict()
        if c.status == "open":
             logger.info("PASS: Conflict model instantiated.")
        else:
             logger.error(f"FAIL: Conflict status is {c.status}")
    except Exception as e:
        logger.error(f"FAIL: Could not instantiate Conflict model: {e}")

    logger.info("--- Verification 110 Complete ---")

if __name__ == "__main__":
    asyncio.run(verify_110())
