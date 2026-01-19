import asyncio
import os
import sys
import logging

# Add backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.db.utils import get_driver
from app.db.crud import (
    create_organization, create_project, create_theme,
    get_organizations, get_projects, get_project_themes,
    archive_organization, reactivate_organization
)
from app.models.domain import WorkspaceStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_verification():
    driver = get_driver()
    
    import uuid
    uid = str(uuid.uuid4())[:8]
    
    # 1. Setup Hierarchy
    logger.info("--- Step 1: Setting up Hierarchy ---")
    org_id = await create_organization(f"Test Org Archival {uid}", "A test organization")
    proj_id = await create_project(f"Test Project {uid}", org_id, "A test project")
    theme_id = await create_theme(proj_id, f"Test Theme {uid}", "A test theme")
    
    logger.info(f"Created Hierarchy: Org={org_id} -> Proj={proj_id} -> Theme={theme_id}")
    
    # Verify Initial Status
    orgs = await get_organizations() # Should contain our org
    test_org = next((o for o in orgs if o['id'] == org_id), None)
    if not test_org or test_org.get('status') != 'active':
        logger.error(f"Initial Org Status Incorrect: {test_org}")
        return

    # 2. Archive Organization
    logger.info("--- Step 2: Archiving Organization ---")
    await archive_organization(org_id)
    
    # Verify Cascading Status (Use include_archived=True to fetch them)
    # Check Org
    orgs_archived = await get_organizations(include_archived=True)
    test_org = next((o for o in orgs_archived if o['id'] == org_id), None)
    if test_org['status'] != 'archived':
         logger.error(f"Org failed to archive: {test_org}")
    
    # Check Project
    projects = await get_projects(org_id, include_archived=True)
    test_proj = next((p for p in projects if p['id'] == proj_id), None)
    if test_proj['status'] != 'archived':
         logger.error(f"Project failed to cascade archive: {test_proj}")
         
    # Check Theme
    themes = await get_project_themes(proj_id, include_archived=True)
    test_theme = next((t for t in themes if t['id'] == theme_id), None)
    if test_theme['status'] != 'archived':
         logger.error(f"Theme failed to cascade archive: {test_theme}")
         
    logger.info("Cascading Archival Verified.")

    # 3. Verify Write Protection
    logger.info("--- Step 3: Verify Write Protection ---")
    try:
        await create_project("Should Fail", org_id)
        logger.error("FAILED: Managed to create project in archived organization!")
    except Exception as e:
        if "archived" in str(e):
             logger.info("SUCCESS: Write protection blocked project creation.")
        else:
             logger.error(f"Unexpected error during write protection test: {e}")

    # 4. Reactivate Organization
    logger.info("--- Step 4: Reactivate Organization ---")
    await reactivate_organization(org_id)
    
    # Verify Org is Active, Children remain Archived
    orgs = await get_organizations()
    test_org = next((o for o in orgs if o['id'] == org_id), None)
    if not test_org: 
        logger.error("Org not visible in active list after reactivation")
    
    projects = await get_projects(org_id) # Should NOT return our project as it is still archived
    visible_proj = next((p for p in projects if p['id'] == proj_id), None)
    if visible_proj:
         logger.error("Project incorrectly visible (should remain archived)")
    else:
         logger.info("Children correctly remained archived.")

    logger.info("--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(run_verification())
