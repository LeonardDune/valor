import asyncio
import os
import sys
import logging
import json

# Add backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.db.utils import get_driver
from app.db.crud import (
    create_organization, create_project, create_theme,
    create_user,
    assign_role, check_permission, get_user_navigation_tree
)
from app.models.domain import Role

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_verification():
    driver = get_driver()
    import uuid
    uid = str(uuid.uuid4())[:8]

    logger.info("--- Step 1: Setting up Hierarchy ---")
    # Hierarchy: Org -> Proj -> Theme
    org_id = await create_organization(f"RBAC Org {uid}", "Test Org")
    proj_id = await create_project(f"RBAC Proj {uid}", org_id, "Test Proj")
    theme_id = await create_theme(proj_id, f"RBAC Theme {uid}", "Test Theme")
    
    # Another Project for isolation test
    other_proj_id = await create_project(f"Isolation Proj {uid}", org_id, "Should be invisible")
    
    logger.info(f"Hierarchy Created: O={org_id}, P={proj_id}, T={theme_id}")

    logger.info("--- Step 2: Test Admin Cascading ---")
    # User A: Org Admin
    user_a_email = f"admin_{uid}@valor.test"
    await create_user(user_a_email, "Admin User")
    await assign_role(user_a_email, org_id, Role.ADMIN)
    
    # Check permissions
    # 1. Direct on Org (Should be True)
    if not await check_permission(user_a_email, org_id, Role.ADMIN):
        logger.error("FAIL: Org Admin missing direct permission")
    else:
        logger.info("PASS: Org Admin has direct permission")
        
    # 2. Cascading on Project (Should be True)
    if not await check_permission(user_a_email, proj_id, Role.ADMIN):
        logger.error("FAIL: Org Admin missing cascading permission on Project")
    else:
        logger.info("PASS: Org Admin has cascading permission on Project")

    # 3. Cascading on Theme (Should be True)
    if not await check_permission(user_a_email, theme_id, Role.MEMBER): # Checking lower role too
        logger.error("FAIL: Org Admin missing cascading permission on Theme")
    else:
        logger.info("PASS: Org Admin has cascading permission on Theme")
        
    logger.info("--- Step 3: Test Theme Admin Isolation ---")
    # User B: Theme Admin (Only)
    user_b_email = f"theme_admin_{uid}@valor.test"
    await create_user(user_b_email, "Theme Admin User")
    await assign_role(user_b_email, theme_id, Role.ADMIN)
    
    # Check permissions
    # 1. Direct on Theme (Should be True)
    if not await check_permission(user_b_email, theme_id, Role.ADMIN):
        logger.error("FAIL: Theme Admin missing direct permission")
    else:
        logger.info("PASS: Theme Admin has direct permission")
        
    # 2. Reverse on Project (Should be False)
    if await check_permission(user_b_email, proj_id, Role.VIEWER):
        logger.error("FAIL: Theme Admin INCORRECTLY has permission on Parent Project")
    else:
        logger.info("PASS: Theme Admin correctly denied permission on Parent Project")

    # 3. Sibling Project (Should be False)
    if await check_permission(user_b_email, other_proj_id, Role.VIEWER):
        logger.error("FAIL: Theme Admin INCORRECTLY has permission on Sibling Project")
    else:
        logger.info("PASS: Theme Admin correctly denied permission on Sibling Project")


    logger.info("--- Step 4: Verify Navigation Tree ---")
    # Tree for Org Admin (Should see EVERYTHING)
    tree_a = await get_user_navigation_tree(user_a_email)
    logger.info(f"Admin Tree: {json.dumps(tree_a, indent=2)}")
    
    # Assertions
    if len(tree_a) != 1: logger.error("FAIL: Admin Tree should have 1 root (Org)")
    elif len(tree_a[0]['children']) != 2: logger.error(f"FAIL: Admin Tree Org should have 2 children (Projects). Found {len(tree_a[0]['children'])}")
    else: logger.info("PASS: Admin Tree structure looks correct")

    # Tree for Theme Admin (Should see Org->Proj->Theme path ONLY)
    tree_b = await get_user_navigation_tree(user_b_email)
    logger.info(f"Theme Admin Tree: {json.dumps(tree_b, indent=2)}")
    
    # Assertions
    # Expecting: Org (container) -> Project (container) -> Theme (active)
    if not tree_b: logger.error("FAIL: Theme Admin Tree empty")
    else:
        root = tree_b[0]
        if root['id'] != org_id: logger.error("FAIL: Theme Admin Tree root mismatch")
        elif len(root['children']) != 1: logger.error("FAIL: Theme Admin Tree should verify isolation (only 1 project path visible)")
        elif root['children'][0]['id'] != proj_id: logger.error("FAIL: Theme Admin Tree project mismatch")
        else: logger.info("PASS: Theme Admin Tree correctly isolated")

    logger.info("--- RBAC Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(run_verification())
