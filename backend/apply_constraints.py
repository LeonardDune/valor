import os
import sys
import logging

# Add backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.db.utils import get_driver

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_constraints():
    driver = get_driver()

    
    constraints = [
        "CREATE CONSTRAINT org_id IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS NODE KEY",
        "CREATE CONSTRAINT project_id IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS NODE KEY",
        "CREATE CONSTRAINT theme_id IF NOT EXISTS FOR (t:Theme) REQUIRE t.id IS NODE KEY"
    ]
    
    try:
        with driver.session() as session:
            for constraint in constraints:
                logger.info(f"Applying constraint: {constraint}")
                session.run(constraint)
        logger.info("All constraints applied successfully.")
    except Exception as e:
        logger.error(f"Failed to apply constraints: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    apply_constraints()
