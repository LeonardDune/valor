import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from app.db.utils import get_driver
from app.models.domain import InviteStatus, Role
from app.db.permissions import check_permission
from neo4j.exceptions import ConstraintError

logger = logging.getLogger(__name__)

async def create_invite(inviter_id: str, target_email: str, entity_id: str, role: Role = Role.MEMBER, expires_in_days: int = 7, redirect_url: Optional[str] = None) -> Dict:
    """
    Creates an invite for a user to join an entity.
    """
    # 1. Check Permissions
    can_invite = await check_permission(inviter_id, entity_id, Role.ADMIN)
    if not can_invite:
        raise Exception(f"User {inviter_id} is not authorized to invite to entity {entity_id}")


    # 2. Supabase Integration (Admin Invite)
    # This sends the email and creates the Auth user
    try: 
        from supabase import create_client, Client
        import os
        
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
        
        if not supabase_key:
             logger.warning("SUPABASE_SERVICE_KEY not found. Skipping Supabase Invite (Local only).")
        else:
            supabase: Client = create_client(supabase_url, supabase_key)
            # Sends invite email and returns user data
            # Note: This creates user in 'invited' state
            
            # Prioritize passed redirect_url, fallback to env, then safe default
            if not redirect_url:
                 raise Exception("Missing required 'redirect_url'. Frontend must provide its origin.")
            
            logger.info(f"DEBUG: Received redirect_url from Frontend: '{redirect_url}'")
            
            final_redirect = redirect_url
            # Ensure it points to the password update page if not already specified
            if "/update-password" not in final_redirect:
                final_redirect = f"{final_redirect.rstrip('/')}/update-password"

            response = supabase.auth.admin.invite_user_by_email(
                target_email, 
                options={"redirectTo": final_redirect}
            )
            logger.info(f"Supabase Invite sent to {target_email} with redirect: {final_redirect}")
            
    except Exception as e:
         # Check for "User already registered" error from Supabase
         error_str = str(e).lower()
         if "already registered" in error_str or "already been registered" in error_str:
             logger.info(f"User {target_email} already exists in Supabase. Proceeding to create local invite.")
         else:
             logger.error(f"Supabase Invite Failed: {e}")
             # Only raise if it's NOT an "already registered" error
             # For other errors (e.g. connection), strictly failing is safer
             raise Exception(f"Failed to send invite email: {e}")

    # 3. Create Local Invite Record
    driver = get_driver()
    invite_code = str(uuid.uuid4())
    expiration = datetime.now() + timedelta(days=expires_in_days)
    
    query = """
    MATCH (inviter:User {id: $inviter_id})
    MATCH (entity {id: $entity_id}) // Match Org, Project, or Theme
    
    CREATE (i:Invite {
        id: randomUUID(),
        email: $target_email,
        code: $code,
        role: $role,
        status: $status,
        created_at: datetime(),
        expires_at: datetime($expires_at)
    })
    
    MERGE (inviter)-[:CREATED]->(i)
    MERGE (i)-[:FOR_ACCESS]->(entity)
    
    RETURN i.id as id, i.code as code
    """
    
    try:
        with driver.session() as session:
            # Note: We pass datetime object as ISO string or supported type if needed, 
            # but Neo4j python driver handles datetime.
            result = session.run(query, {
                "inviter_id": inviter_id,
                "entity_id": entity_id,
                "target_email": target_email,
                "code": invite_code,
                "role": role.value,
                "status": InviteStatus.PENDING.value,
                "expires_at": expiration
            })
            record = result.single()
            if not record:
                 # Check if entity exists
                 raise Exception(f"Entity {entity_id} not found or Inviter {inviter_email} not found.")
            
            logger.info(f"Invite created for {target_email} to {entity_id}")
            return {"id": record["id"], "code": record["code"]}
            
    except Exception as e:
        logger.error(f"Failed to create invite: {e}")
        raise e

async def get_pending_invites(entity_id: str) -> List[Dict]:
    driver = get_driver()
    query = """
    MATCH (i:Invite)-[:FOR_ACCESS]->(e {id: $eid})
    WHERE i.status = $status
    RETURN i.id as id, i.email as email, i.role as role, i.created_at as created_at, i.expires_at as expires_at, i.code as code
    ORDER BY i.created_at DESC
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"eid": entity_id, "status": InviteStatus.PENDING.value})
            invites = []
            for record in result:
                data = dict(record)
                # Convert Neo4j DateTime to ISO string
                if data.get("created_at"):
                    data["created_at"] = data["created_at"].iso_format()
                if data.get("expires_at"):
                    data["expires_at"] = data["expires_at"].iso_format()
                invites.append(data)
            return invites
    except Exception as e:
        logger.error(f"Failed to get pending invites: {e}")
        return []

async def accept_invite(code: str, user_id: str, user_email: str) -> Dict:
    """
    User uses the code to accept. 
    We verify code, expiration, and email match.
    Then create MEMBER_OF relationship.
    """
    driver = get_driver() # Fixed validation
    
    # Transactional logic
    query = """
    MATCH (i:Invite {code: $code})
    WHERE i.status = 'pending' AND i.expires_at > datetime()
    
    // Validate User
    MATCH (u:User {id: $uid})
    
    // Check Email Match (Optional: enforce strict match)
    // WHERE i.email = $email // Enforce this? Yes, security.
    
    WITH i, u
    WHERE i.email = $email
    
    MATCH (i)-[:FOR_ACCESS]->(entity)
    
    // Create Role
    MERGE (u)-[r:HAS_ROLE]->(entity)
    ON CREATE SET r.role = i.role, r.joined_at = datetime()
    ON MATCH SET r.role = i.role // Update role if exists?
    
    // Update Invite
    SET i.status = 'accepted', i.accepted_at = datetime()
    
    RETURN entity.id as entity_id, entity.name as entity_name, i.role as role
    """
    
    try:
        with driver.session() as session:
            result = session.run(query, {"code": code, "email": user_email, "uid": user_id})
            record = result.single()
            
            if not record:
                # Need to find out why failed: Expiration? Code? Email mismatch?
                # For now generic error, improving logging recommended.
                # Let's do a quick check to give better error
                check_q = "MATCH (i:Invite {code: $code}) RETURN i.status, i.expires_at, i.email"
                res = session.run(check_q, {"code": code}).single()
                if not res:
                     raise Exception("Invalid Invite Code")
                if res["i.status"] != "pending":
                     raise Exception("Invite already accepted or invalid")
                # Expiration check in python for clarity
                # Neo4j datetime object handling might differ, let's rely on query logic
                if res["i.email"] != user_email:
                     raise Exception(f"This invite is for {res['i.email']}, not {user_email}")
                
                raise Exception("Invite expired or failed to process.")

            return {
                "status": "accepted", 
                "entity_id": record["entity_id"], 
                "role": record["role"]
            }
            
    except Exception as e:
        logger.error(f"Failed to accept invite: {e}")
        raise e

async def claim_pending_invites(user_id: str, user_email: str) -> List[Dict]:
    """
    Automatically accepts any pending invites for this email.
    Called on dashboard load to ensure roles are synced if user just signed up via invite.
    """
    driver = get_driver()
    query = """
    MATCH (i:Invite {email: $email, status: 'pending'})
    WHERE i.expires_at > datetime()
    
    // Validate User
    MATCH (u:User {id: $uid})
    
    // Ensure User email matches Invite email (implicit via $email passed for Invite match, 
    // but strictly checking User properties might be needed if email on User node differs from Auth email?
    // Assuming synced. But here we match User by ID.
    
    MATCH (i)-[:FOR_ACCESS]->(entity)
    
    // Create Role
    MERGE (u)-[r:HAS_ROLE]->(entity)
    ON CREATE SET r.role = i.role, r.joined_at = datetime()
    ON MATCH SET r.role = i.role
    
    // Update Invite
    SET i.status = 'accepted', i.accepted_at = datetime()
    
    RETURN entity.id as entity_id, entity.name as entity_name, i.role as role
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"email": user_email, "uid": user_id})
            claimed = []
            for record in result:
                logger.info(f"Auto-claimed invite for {user_email} to {record['entity_name']} ({record['entity_id']})")
                claimed.append(dict(record))
            return claimed
    except Exception as e:
        logger.error(f"Failed to auto-claim invites: {e}")
        return []
