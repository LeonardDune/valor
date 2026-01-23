import asyncio
import logging
import uuid
import sys
import os

# Adjust path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.utils import get_driver, close_driver
from app.db.crud import create_organization, create_user, add_user_to_organization, get_user_by_email
from app.db.invites import create_invite, accept_invite, get_pending_invites
from app.models.domain import Role, InviteStatus

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_verification():
    logger.info("--- Starting Invite System Verification ---")
    
    # Setup: Create Org and Admin
    org_name = f"Invite Org {uuid.uuid4().hex[:8]}"
    admin_email = f"admin_{uuid.uuid4().hex[:8]}@test.com"
    
    logger.info(f"Creating Org: {org_name} with Admin: {admin_email}")
    org_id = await create_organization(org_name, "Test description", owner_email=admin_email)
    
    # 1. Hybrid Invite: Existing User -> Direct Add
    existing_user_email = f"existing_{uuid.uuid4().hex[:8]}@test.com"
    await create_user(existing_user_email, "Existing User")
    
    logger.info("Test 1: Hybrid Invite (Existing User)")
    # Simulate API Logic check
    existing_user = await get_user_by_email(existing_user_email)
    if existing_user:
        await add_user_to_organization(existing_user_email, org_id, Role.MEMBER)
        logger.info("PASS: Added existing user directly")
    else:
        logger.error("FAIL: Could not find existing user")

    # Verify Membership
    driver = get_driver()
    with driver.session() as session:
        res = session.run("MATCH (u:User {email: $email})-[:HAS_ROLE]->(o:Organization {id: $oid}) RETURN u", 
                          {"email": existing_user_email, "oid": org_id})
        if res.single():
            logger.info("PASS: Existing user is Member")
        else:
            logger.error("FAIL: Existing user NOT linked")

    # 2. Hybrid Invite: Non-Existing User -> Create Invite
    new_user_email = f"new_{uuid.uuid4().hex[:8]}@test.com"
    logger.info("Test 2: Create Invite (New User)")
    
    invite_result = await create_invite(admin_email, new_user_email, org_id, Role.MEMBER)
    invite_code = invite_result['code']
    logger.info(f"Invite Created. Code: {invite_code}")

    # Verify Pending List
    pending = await get_pending_invites(org_id)
    if any(i['email'] == new_user_email for i in pending):
        logger.info("PASS: Invite found in Pending List")
    else:
        logger.error("FAIL: Invite NOT found in Pending List")

    # 3. Accept Invite
    logger.info("Test 3: Accept Invite")
    # First create the "New" user (simulating Supabase registration)
    await create_user(new_user_email, "New User Registered")
    
    accept_result = await accept_invite(invite_code, new_user_email)
    logger.info(f"Accept Result: {accept_result}")
    
    # Verify Membership
    with driver.session() as session:
        res = session.run("MATCH (u:User {email: $email})-[:HAS_ROLE]->(o:Organization {id: $oid}) RETURN u", 
                          {"email": new_user_email, "oid": org_id})
        if res.single():
            logger.info("PASS: New user is Member after acceptance")
        else:
            logger.error("FAIL: New user NOT linked after acceptance")

    # Verify Invite Status is Accepted
    with driver.session() as session:
        check_invite = session.run("MATCH (i:Invite {code: $code}) RETURN i.status as status", {"code": invite_code}).single()
        if check_invite and check_invite["status"] == InviteStatus.ACCEPTED.value:
             logger.info("PASS: Invite status is ACCEPTED")
        else:
             logger.error(f"FAIL: Invite status is {check_invite['status'] if check_invite else 'None'}")

    # 4. Expiration Logic (Optional check)
    # create expired invite... (Requires modifying create_invite to accept expired date or mocking time, skipping for now)

    logger.info("--- Verification Complete ---")
    close_driver()

if __name__ == "__main__":
    asyncio.run(run_verification())
