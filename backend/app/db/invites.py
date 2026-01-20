import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from app.db.utils import get_driver
from app.models.domain import InviteStatus, Role
from app.db.permissions import check_permission
from neo4j.exceptions import ConstraintError

logger = logging.getLogger(__name__)

async def create_invite(inviter_email: str, target_email: str, entity_id: str, role: Role = Role.MEMBER, expires_in_days: int = 7) -> Dict:
    """
    Creates an invite for a user to join an entity.
    If user exists, it MIGHT define direct add logic (hybrid), 
    but per plan we rely on this function primarily for the 'Pending' flow 
    or just creating the Invite node regardless.
    
    Start by checking if Inviter has Admin rights.
    """
    # 1. Check Permissions
    can_invite = await check_permission(inviter_email, entity_id, Role.ADMIN)
    if not can_invite:
        raise Exception(f"User {inviter_email} is not authorized to invite to entity {entity_id}")

    driver = get_driver()
    invite_code = str(uuid.uuid4())
    expiration = datetime.now() + timedelta(days=expires_in_days)
    
    # 2. Check if user exists (Hybrid Logic)
    # We'll return a specific status if user was directly added, 
    # but for now, let's stick to creating the Invite Node + Email Flow logic 
    # as the primary request was "Invite". 
    # If the user exists, they still need to 'accept' strictly speaking 
    # unless we want auto-add. 
    # Let's Implement: create Invite Node ALWAYS. 
    # The frontend/user can decide to auto-accept if they handle the flow differently.
    
    query = """
    MATCH (inviter:User {email: $inviter_email})
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
                "inviter_email": inviter_email,
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
            return [dict(record) for record in result]
    except Exception as e:
        logger.error(f"Failed to get pending invites: {e}")
        return []

async def accept_invite(code: str, user_email: str) -> Dict:
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
    MATCH (u:User {email: $email})
    
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
            result = session.run(query, {"code": code, "email": user_email})
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
