import asyncio
import os
import sys
import logging
import json
import uuid

# Add backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.db.utils import get_driver
from app.db.crud import (
    create_organization, create_project, create_theme,
    create_user, assign_role, check_permission,
    get_organization_users, get_project_users, get_theme_users, get_all_users
)
from app.models.domain import Role, User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_verification():
    driver = get_driver()
    uid = str(uuid.uuid4())[:8]

    logger.info(f"--- Step 1: Setting up Test Environment ({uid}) ---")
    
    # 1. Organization A Structure
    org_a_id = await create_organization(f"Org A {uid}", "Organization A")
    proj_a1_id = await create_project(f"Proj A1 {uid}", org_a_id, "Project A1")
    theme_a1_1_id = await create_theme(proj_a1_id, f"Theme A1-1 {uid}", "Theme A1-1")
    
    # 2. Organization B Structure (for isolation)
    org_b_id = await create_organization(f"Org B {uid}", "Organization B")
    
    # 3. Create Users
    # Platform Admin
    admin_email = f"platform_admin_{uid}@valor.test"
    admin_user = await create_user(admin_email, "Platform Admin")
    # Manually set is_platform_admin in Neo4j (since create_user doesn't set it)
    with driver.session() as session:
        session.run("MATCH (u:User {email: $email}) SET u.is_platform_admin = true", email=admin_email)
    
    # Org A Admin
    user_org_a_email = f"org_a_admin_{uid}@valor.test"
    await create_user(user_org_a_email, "Org A Admin")
    await assign_role(user_org_a_email, org_a_id, Role.ADMIN)
    
    # Project A1 Member
    user_proj_a1_email = f"proj_a1_member_{uid}@valor.test"
    await create_user(user_proj_a1_email, "Project A1 Member")
    await assign_role(user_proj_a1_email, proj_a1_id, Role.MEMBER)
    
    # Theme A1-1 Member
    user_theme_a1_email = f"theme_a1_member_{uid}@valor.test"
    await create_user(user_theme_a1_email, "Theme A1-1 Member")
    await assign_role(user_theme_a1_email, theme_a1_1_id, Role.MEMBER)
    
    # Org B Member
    user_org_b_email = f"org_b_member_{uid}@valor.test"
    await create_user(user_org_b_email, "Org B Member")
    await assign_role(user_org_b_email, org_b_id, Role.MEMBER)

    logger.info("Environment setup complete.")

    logger.info("\n--- Step 2: Verifying Scoped Member Retrieval ---")
    
    # 1. Org A Users
    org_a_users = await get_organization_users(org_a_id)
    # Should include Org Admin, AND potentially Project/Theme users if cascading? 
    # Current logic: `(:User)-[r:HAS_ROLE]->(o:Organization)`. So only direct Org members.
    logger.info(f"Org A Users count: {len(org_a_users)}")
    if not any(u['email'] == user_org_a_email for u in org_a_users):
        logger.error("FAIL: Org Admin not found in Org A users")
    else:
        logger.info("PASS: Org Admin found in Org A users")

    # 2. Project A1 Users
    proj_a1_users = await get_project_users(proj_a1_id)
    logger.info(f"Project A1 Users count: {len(proj_a1_users)}")
    if not any(u['email'] == user_proj_a1_email for u in proj_a1_users):
        logger.error("FAIL: Project Member not found in Project A1 users")
    else:
        logger.info("PASS: Project Member found in Project A1 users")
        
    # 3. Theme A1-1 Users
    theme_a1_users = await get_theme_users(theme_a1_1_id)
    logger.info(f"Theme A1-1 Users count: {len(theme_a1_users)}")
    if not any(u['email'] == user_theme_a1_email for u in theme_a1_users):
        logger.error("FAIL: Theme Member not found in Theme A1-1 users")
    else:
        logger.info("PASS: Theme Member found in Theme A1-1 users")

    logger.info("\n--- Step 3: Verifying Permission Enforcement (The 'Strict Visibility' Check) ---")
    
    # 1. User Project A1 Member accessing Project A1 -> SHOULD ALLOW
    has_perm = await check_permission(user_proj_a1_email, proj_a1_id, Role.MEMBER)
    if has_perm:
        logger.info("PASS: Project Member has access to Project A1")
    else:
        logger.error("FAIL: Project Member denied access to Project A1")

    # 2. User Project A1 Member accessing Org A -> SHOULD DENY (Role is on Project, not Org)
    has_perm = await check_permission(user_proj_a1_email, org_a_id, Role.MEMBER)
    if not has_perm:
        logger.info("PASS: Project Member correctly denied access to parent Org A")
    else:
        logger.error("FAIL: Project Member INCORRECTLY allowed access to parent Org A")

    # 3. User Project A1 Member accessing Org B -> SHOULD DENY
    has_perm = await check_permission(user_proj_a1_email, org_b_id, Role.VIEWER)
    if not has_perm:
        logger.info("PASS: Project Member correctly denied access to Org B")
    else:
        logger.error("FAIL: Project Member INCORRECTLY allowed access to Org B")
        
    # 4. User Theme A1-1 Member accessing Project A1 -> SHOULD DENY
    has_perm = await check_permission(user_theme_a1_email, proj_a1_id, Role.VIEWER)
    if not has_perm:
        logger.info("PASS: Theme Member correctly denied access to parent Project A1")
    else:
        logger.error("FAIL: Theme Member INCORRECTLY allowed access to parent Project A1")
        
    logger.info("\n--- Step 4: Verifying Platform Admin Access ---")
    
    # 1. Platform Admin accessing Org A (without explicit role) -> SHOULD ALLOW
    # Note: check_permission logic should handle is_platform_admin bypassing
    has_perm = await check_permission(admin_email, org_a_id, Role.ADMIN)
    if has_perm:
        logger.info("PASS: Platform Admin allowed access to Org A (bypass)")
    else:
        logger.error("FAIL: Platform Admin denied access to Org A")
        
    # 2. Platform Admin retrieving ALL users
    all_users = await get_all_users()
    logger.info(f"Total Users in System: {len(all_users)}")
    
    # Should find all our created users
    emails_to_find = [admin_email, user_org_a_email, user_proj_a1_email, user_theme_a1_email, user_org_b_email]
    found_count = sum(1 for u in all_users if u['email'] in emails_to_find)
    
    if found_count == len(emails_to_find):
        logger.info("PASS: Platform Admin sees all created users")
    else:
        logger.error(f"FAIL: Platform Admin missed some users. Found {found_count}/{len(emails_to_find)}")

    logger.info("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(run_verification())
