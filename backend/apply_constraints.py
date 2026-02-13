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
        # Legacy constraints (Keep until full cleanup)
        "CREATE CONSTRAINT theme_id IF NOT EXISTS FOR (t:Theme) REQUIRE t.id IS NODE KEY",
        
        # New Schema Constraints
        "CREATE CONSTRAINT theme_base_id IF NOT EXISTS FOR (tb:ThemeBase) REQUIRE tb.id IS NODE KEY",
        "CREATE CONSTRAINT theme_version_id IF NOT EXISTS FOR (tv:ThemeVersion) REQUIRE tv.id IS NODE KEY",
        "CREATE CONSTRAINT factor_base_id IF NOT EXISTS FOR (fb:FactorBase) REQUIRE fb.id IS NODE KEY",
        "CREATE CONSTRAINT factor_version_id IF NOT EXISTS FOR (fv:FactorVersion) REQUIRE fv.id IS NODE KEY",
        "CREATE CONSTRAINT claim_base_id IF NOT EXISTS FOR (cb:ClaimBase) REQUIRE cb.id IS NODE KEY",
        "CREATE CONSTRAINT claim_version_id IF NOT EXISTS FOR (cv:ClaimVersion) REQUIRE cv.id IS NODE KEY"
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
