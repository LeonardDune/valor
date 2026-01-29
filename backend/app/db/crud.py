from typing import List, Optional, Dict, Any
import uuid
import logging
from datetime import datetime
from app.db.utils import get_driver
from app.models.domain import Role, LifecycleStatus, Claim, Factor, Proposal
from app.db.permissions import check_permission

# Re-export get_driver for main.py compatibility
# from app.db.utils import get_driver (already imported)

logger = logging.getLogger(__name__)

# --- Agent / Conversation ---

async def save_claims(conversation_id: str, claims: List[Claim]):
    """
    Persists claims extracted by the Agent.
    Creates Factor nodes if they don't exist.
    Creates / Updates relationships using reified schema.
    """
    driver = get_driver()
    query = """
    MERGE (ct:ConversationThread {id: $cid})
    WITH ct, ct.topic as theme_id
    UNWIND $claims as claim
    
    // Merge Source
    MERGE (source:Factor {name: claim.source_node})
    ON CREATE SET source.id = randomUUID(), source.type = coalesce(claim.source_type, 'systeemelement'), source.created_at = datetime()
    
    // Merge Target
    MERGE (target:Factor {name: claim.target_node})
    ON CREATE SET target.id = randomUUID(), target.type = coalesce(claim.target_type, 'systeemelement'), target.created_at = datetime()
    
    // Create Reified Relationship (Claim node + links)
    MERGE (c:Claim {id: claim.id})
    SET c.statement = claim.statement,
        c.confidence = claim.confidence,
        c.polarity = claim.polarity,
        c.relationship_type = coalesce(claim.relationship_type, 'CAUSES'),
        c.created_at = datetime()
        
    MERGE (source)-[:CLAIMS]->(c)
    MERGE (c)-[:TO]->(target)
    
    // Link to Conversation
    MERGE (ct)-[:GENERATED]->(c)

    // Robust Linking: If conversation has a topic (Theme ID), link factors to that Theme
    WITH source, target, theme_id
    WHERE theme_id IS NOT NULL
    MATCH (t:Theme {id: theme_id})
    MERGE (t)-[:HAS_FACTOR]->(source)
    MERGE (t)-[:HAS_FACTOR]->(target)
    """
    
    # Transform claims to dicts
    claims_data = []
    for c in claims:
        # Use .dict() if Pydantic, else __dict__
        c_dict = c.dict() if hasattr(c, 'dict') else c.__dict__ if hasattr(c, '__dict__') else c
        # Ensure ID
        if isinstance(c_dict, dict) and not c_dict.get('id'): c_dict['id'] = str(uuid.uuid4())
        claims_data.append(c_dict)

    try:
        with driver.session() as session:
            session.run(query, {"cid": conversation_id, "claims": claims_data})
    except Exception as e:
        logger.error(f"Failed to save claims: {e}")

async def set_conversation_topic(conversation_id: str, topic: str):
    driver = get_driver()
    query = """
    MERGE (c:ConversationThread {id: $cid})
    SET c.topic = $topic, c.updated_at = datetime()
    """
    try:
        with driver.session() as session:
            session.run(query, {"cid": conversation_id, "topic": topic})
    except Exception as e:
        logger.error(f"Failed to set topic: {e}")

async def get_conversation_topic(conversation_id: str) -> Optional[str]:
    driver = get_driver()
    query = "MATCH (c:ConversationThread {id: $cid}) RETURN c.topic as topic"
    try:
        with driver.session() as session:
            result = session.run(query, {"cid": conversation_id})
            record = result.single()
            return record["topic"] if record else None
    except Exception as e:
        return None

async def fetch_existing_factors(conversation_id: str) -> List[str]:
    """Returns names of factors mentioned in this conversation or context."""
    driver = get_driver()
    query = """
    MATCH (c:ConversationThread {id: $cid})-[:GENERATED]->(cl:Claim)
    MATCH (source)-[:CLAIMS]->(cl)-[:TO]->(target)
    RETURN collect(distinct source.name) + collect(distinct target.name) as factors
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"cid": conversation_id})
            record = result.single()
            if record:
                # flatten and distinct
                names = list(set(record["factors"]))
                return names
            return []
    except Exception as e:
        logger.error(f"Failed to fetch factors: {e}")
        return []

async def revoke_claims(conversation_id: str):
    """Marks claims from this conversation as revoked or deletes them?"""
    driver = get_driver()
    query = """
    MATCH (c:ConversationThread {id: $cid})-[rel:GENERATED]->(cl:Claim)
    DETACH DELETE cl
    """
    try:
        with driver.session() as session:
            session.run(query, {"cid": conversation_id})
    except Exception as e:
        logger.error(f"Failed to revoke claims: {e}")

# --- Proposals (Restored) ---

async def create_proposal(title: str, author_id: str, description: Optional[str] = None, type: str = "standard", target_id: Optional[str] = None) -> str:
    driver = get_driver()
    proposal_id = str(uuid.uuid4())
    
    query = """
    MATCH (u:User {id: $author_id}) # Expecting internal ID, or match by email if author_id is email?
    # Usually author_id is passed as internal ID from get_current_user logic if available, 
    # but currently our user/auth system uses email often. 
    # Let's assume author_id is ID. If fails, we might need to MATCH by email?
    # In main.py create_proposal uses request.author_id.
    
    CREATE (p:Proposal {
        id: $id,
        title: $title,
        description: $description,
        type: $type,
        target_id: $target_id,
        status: 'proposed',
        created_at: datetime()
    })
    CREATE (u)-[:CREATED]->(p)
    RETURN p.id as id
    """
    # Fallback if author_id is actually an email (common in this codebase transitions)
    # logic: try match by id, if not found try match by email? 
    # Cypher: MATCH (u:User) WHERE u.id = $aid OR u.email = $aid
    
    query = """
    MATCH (u:User) WHERE u.id = $author_id OR u.email = $author_id
    WITH u LIMIT 1
    CREATE (p:Proposal {
        id: $id,
        title: $title,
        description: $description,
        type: $type,
        target_id: $target_id,
        status: 'proposed',
        created_at: datetime()
    })
    CREATE (u)-[:CREATED]->(p)
    RETURN p.id as id
    """

    try:
        with driver.session() as session:
            result = session.run(query, {
                "id": proposal_id,
                "title": title,
                "author_id": author_id,
                "description": description,
                "type": type,
                "target_id": target_id
            })
            record = result.single()
            if record:
                return record["id"]
            raise Exception("User not found or creation failed")
    except Exception as e:
        logger.error(f"Error creating proposal: {e}")
        raise e

async def get_proposals(status: Optional[str] = None, author_id: Optional[str] = None) -> List[Proposal]:
    driver = get_driver()
    
    query = """
    MATCH (p:Proposal)<-[:CREATED]-(u:User)
    """
    
    where_clauses = []
    params = {}
    
    if status:
        where_clauses.append("p.status = $status")
        params["status"] = status
        
    if author_id:
        where_clauses.append("(u.id = $author_id OR u.email = $author_id)")
        params["author_id"] = author_id

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
        
    query += """
    RETURN p, u.id as author_id
    ORDER BY p.created_at DESC
    """
    
    try:
        with driver.session() as session:
            result = session.run(query, params)
            proposals = []
            for record in result:
                node = record["p"]
                auth_id = record["author_id"]
                proposals.append(Proposal(
                    id=node["id"],
                    title=node["title"],
                    description=node.get("description"),
                    status=LifecycleStatus(node.get("status", "draft")),
                    author_id=auth_id,
                    type=node.get("type"),
                    target_id=node.get("target_id"),
                    created_at=str(node["created_at"])
                ))
            return proposals
    except Exception as e:
        logger.error(f"Error getting proposals: {e}")
        return []

async def get_proposal_by_id(proposal_id: str) -> Optional[Proposal]:
    driver = get_driver()
    query = """
    MATCH (p:Proposal {id: $id})<-[:CREATED]-(u:User)
    RETURN p, u.id as author_id
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"id": proposal_id})
            record = result.single()
            if record:
                node = record["p"]
                return Proposal(
                    id=node["id"],
                    title=node["title"],
                    description=node.get("description"),
                    status=LifecycleStatus(node.get("status", "draft")),
                    author_id=record["author_id"],
                    type=node.get("type"),
                    target_id=node.get("target_id"),
                    created_at=str(node["created_at"])
                )
            return None
    except Exception as e:
        logger.error(f"Error getting proposal {proposal_id}: {e}")
        return None

async def update_proposal_status(proposal_id: str, status: LifecycleStatus) -> bool:
    driver = get_driver()
    query = """
    MATCH (p:Proposal {id: $id})
    SET p.status = $status
    RETURN p
    """
    try:
        with driver.session() as session:
            status_str = status.value if hasattr(status, 'value') else status
            result = session.run(query, {"id": proposal_id, "status": status_str})
            return result.single() is not None
    except Exception as e:
        logger.error(f"Error updating proposal status: {e}")
        return False

# --- Organization / User Core ---

async def create_organization(name: str, description: Optional[str] = None, owner_id: Optional[str] = None) -> str:
    driver = get_driver()
    org_id = str(uuid.uuid4())
    
    # Logic: Create Org. If owner_id provided, make them Admin.
    query = """
    CREATE (o:Organization {id: $id, name: $name, description: $desc, created_at: datetime(), status: 'active'})
    WITH o
    """
    
    if owner_id:
        query += """
        MATCH (u:User {id: $uid})
        MERGE (u)-[:HAS_ROLE {role: 'admin', updated_at: datetime()}]->(o)
        """
        
    query += " RETURN o.id as id"

    try:
        with driver.session() as session:
            result = session.run(query, {"id": org_id, "name": name, "desc": description, "uid": owner_id})
            record = result.single()
            return record["id"]
    except Exception as e:
        logger.error(f"Error creating org: {e}")
        raise e

async def get_organizations() -> List[Dict]:
    """Returns all organizations (for platform admin use mainly)."""
    driver = get_driver()
    query = """
    MATCH (o:Organization)
    WHERE o.status IS NULL OR o.status <> 'archived' 
    RETURN o
    """
    try:
        with driver.session() as session:
            result = session.run(query)
            return [dict(record["o"]) for record in result]
    except Exception as e:
        logger.error(f"Error listing orgs: {e}")
        return []

async def get_user_organizations(email: str) -> List[Dict]:
    """Returns orgs for a specific user."""
    driver = get_driver()
    query = """
    MATCH (u:User {email: toLower($email)})
    MATCH (u)-[:HAS_ROLE]->(o:Organization)
    WHERE o.status IS NULL OR o.status <> 'archived'
    RETURN o
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"email": email})
            return [dict(record["o"]) for record in result]
    except Exception as e:
        return []

async def create_user(email: str, name: Optional[str] = None, user_id: Optional[str] = None) -> str:
    driver = get_driver()
    uid = user_id if user_id else str(uuid.uuid4())
    query = """
    MERGE (u:User {email: toLower($email)})
    ON CREATE SET u.id = $id, u.name = $name, u.created_at = datetime()
    ON MATCH SET u.name = coalesce($name, u.name)
    RETURN u.id as id
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"email": email, "id": uid, "name": name})
            return result.single()["id"]
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise e

async def get_user_by_id(user_id: str) -> Optional[Dict]:
    driver = get_driver()
    query = "MATCH (u:User {id: $uid}) RETURN u"
    try:
        with driver.session() as session:
            result = session.run(query, {"uid": user_id})
            record = result.single()
            return dict(record["u"]) if record else None
    except Exception as e:
        logger.error(f"Error getting user by id: {e}")
        return None

async def ensure_user_sync(user_id: str, email: str, name: Optional[str] = None) -> Dict:
    """
    Ensures the user exists in Neo4j with the correct Supabase ID (sub).
    Propagates migration if user exists by email but has a different/legacy ID.
    """
    driver = get_driver()
    
    # 1. Try to find by ID (Happy Path)
    user = await get_user_by_id(user_id)
    if user:
        # Update metadata if needed (e.g. email change in Supabase)
        if user.get("email") != email or (name and user.get("name") != name):
            query = "MATCH (u:User {id: $uid}) SET u.email = $email, u.name = coalesce($name, u.name) RETURN u"
            with driver.session() as session:
                session.run(query, {"uid": user_id, "email": email, "name": name})
        return user

    # 2. Not found by ID -> Check for Legacy User by Email (Migration Path)
    legacy_user = await get_user_by_email(email)
    if legacy_user:
        logger.info(f"Migrating user {email} from legacy ID {legacy_user['id']} to Supabase ID {user_id}")
        query = """
        MATCH (u:User {email: toLower($email)})
        SET u.id = $uid, u.updated_at = datetime(), u.migration_status = 'migrated_to_supabase_id'
        RETURN u
        """
        with driver.session() as session:
            result = session.run(query, {"email": email, "uid": user_id})
            record = result.single()
            return dict(record["u"])

    # 3. New User (Registration Path)
    logger.info(f"Creating new user {email} with Supabase ID {user_id}")
    query = """
    MERGE (u:User {id: $uid})
    ON CREATE SET u.email = toLower($email), u.name = $name, u.created_at = datetime()
    ON MATCH SET u.email = toLower($email), u.name = coalesce($name, u.name)
    RETURN u
    """
    with driver.session() as session:
        result = session.run(query, {"uid": user_id, "email": email, "name": name})
        record = result.single()
        return dict(record["u"])

async def get_user_by_email(email: str) -> Optional[Dict]:
    driver = get_driver()
    query = "MATCH (u:User {email: toLower($email)}) RETURN u"
    try:
        with driver.session() as session:
            result = session.run(query, {"email": email})
            record = result.single()
            return dict(record["u"]) if record else None
    except Exception as e:
        return None

async def get_all_users() -> List[Dict]:
    driver = get_driver()
    query = "MATCH (u:User) RETURN u"
    try:
        with driver.session() as session:
            return [dict(r["u"]) for r in session.run(query)]
    except Exception:
        return []

async def update_user_profile(email: str, first_name: str, last_name: str, username: str):
    driver = get_driver()
    query = """
    MATCH (u:User {email: toLower($email)})
    SET u.first_name = $fn, u.last_name = $ln, u.username = $un
    """
    with driver.session() as session:
        session.run(query, {"email": email, "fn": first_name, "ln": last_name, "un": username})

# --- Members ---

async def get_organization_users(org_id: str) -> List[Dict]:
    driver = get_driver()
    query = """
    MATCH (o:Organization {id: $oid})<-[r:HAS_ROLE]-(u:User)
    RETURN u, r.role as role
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"oid": org_id})
            users = []
            for rec in result:
                u = dict(rec["u"])
                u["role"] = rec["role"]
                users.append(u)
            return users
    except Exception as e:
        return []

async def add_user_to_organization(email: str, org_id: str, role: str):
    # Ensure user
    await create_user(email)
    driver = get_driver()
    query = """
    MATCH (u:User {email: toLower($email)})
    MATCH (o:Organization {id: $oid})
    MERGE (u)-[r:HAS_ROLE]->(o)
    SET r.role = $role, r.updated_at = datetime()
    """
    with driver.session() as session:
        session.run(query, {"email": email, "oid": org_id, "role": role})

async def update_org_member_role(org_id: str, user_id: str, role: str, name: Optional[str] = None):
    driver = get_driver()
    query = """
    MATCH (o:Organization {id: $oid})<-[r:HAS_ROLE]-(u:User {id: $uid})
    SET r.role = $role, r.updated_at = datetime()
    """
    if name:
        query += ", u.name = $name"
        
    with driver.session() as session:
        session.run(query, {"oid": org_id, "uid": user_id, "role": role, "name": name})

async def remove_user_from_organization(org_id: str, user_id: str):
    driver = get_driver()
    query = """
    MATCH (o:Organization {id: $oid})<-[r:HAS_ROLE]-(u:User {id: $uid})
    DELETE r
    """
    with driver.session() as session:
        session.run(query, {"oid": org_id, "uid": user_id})

# Project/Theme Members shortcuts (similar logic)
async def get_project_users(project_id: str) -> List[Dict]:
    driver = get_driver()
    query = "MATCH (p:Project {id: $pid})<-[r:HAS_ROLE]-(u:User) RETURN u, r.role as role"
    with driver.session() as session:
         return [{"id": rec["u"]["id"], "name": rec["u"].get("name",""), "email": rec["u"]["email"], "role": rec["role"]} for rec in session.run(query, {"pid": project_id})]

async def update_project_member_role(project_id: str, user_id: str, role: str, name: Optional[str] = None):
     await update_org_member_role(project_id, user_id, role, name) # Generic enough if ID is unique

async def remove_project_member(project_id: str, user_id: str):
    await remove_user_from_organization(project_id, user_id) # Generic

async def get_theme_users(theme_id: str) -> List[Dict]:
     driver = get_driver()
     query = "MATCH (t:Theme {id: $tid})<-[r:HAS_ROLE]-(u:User) RETURN u, r.role as role"
     with driver.session() as session:
         return [{"id": rec["u"]["id"], "name": rec["u"].get("name",""), "email": rec["u"]["email"], "role": rec["role"]} for rec in session.run(query, {"tid": theme_id})]

async def update_theme_member_role(theme_id: str, user_id: str, role: str, name: Optional[str] = None):
     await update_org_member_role(theme_id, user_id, role, name)

async def remove_theme_member(theme_id: str, user_id: str):
     await remove_user_from_organization(theme_id, user_id)
     
# --- Projects / Themes Structure ---

async def get_projects(organization_id: str, user_id: str) -> List[Dict]:
    driver = get_driver()
    query = """
    MATCH (org:Organization {id: $oid})
    MATCH (u:User {id: $uid})
    
    // Determine user role in Organization
    OPTIONAL MATCH (u)-[r_org:HAS_ROLE]->(org)
    WITH org, u, coalesce(r_org.role, 'member') as org_role_direct
    WITH org, u,
         CASE WHEN u.is_platform_admin = true OR org_role_direct = 'admin' THEN 'admin' ELSE 'member' END as org_role
    
    // Find projects
    MATCH (org)-[:OWNS]->(p:Project)
    WHERE p.status IS NULL OR p.status <> 'archived'
    
    // Determine project role (cascade from org)
    OPTIONAL MATCH (u)-[r_proj:HAS_ROLE]->(p)
    WITH org, u, org_role, p, 
         CASE 
            WHEN org_role = 'admin' THEN 'admin'
            ELSE coalesce(r_proj.role, 'member')
         END as proj_role
         
    // Count Themes
    OPTIONAL MATCH (p)-[:HAS_THEME]->(t:Theme)
    WHERE t.status IS NULL OR t.status <> 'archived'
    WITH p, proj_role, org, collect(t) as themes
    
    RETURN {
        id: p.id,
        name: p.name,
        description: p.description,
        organization_name: org.name,
        organization_id: org.id,
        role: proj_role,
        status: p.status,
        type: 'PROJECT',
        themes: themes, 
        created_at: toString(p.created_at)
    } as project_data
    """
    with driver.session() as session:
        return [r["project_data"] for r in session.run(query, {"oid": organization_id, "uid": user_id})]

async def create_project(name: str, organization_id: str, description: Optional[str] = None, owner_id: Optional[str] = None) -> str:
    driver = get_driver()
    pid = str(uuid.uuid4())
    query = """
    MATCH (o:Organization {id: $oid})
    """
    
    if owner_id:
        query += """
        MATCH (u:User {id: $uid})
        CREATE (p:Project {id: $id, name: $name, description: $desc, created_at: datetime(), status: 'active'})
        CREATE (o)-[:OWNS]->(p)
        CREATE (u)-[:HAS_ROLE {role: 'admin'}]->(p)
        """
    else:
        query += """
        CREATE (p:Project {id: $id, name: $name, description: $desc, created_at: datetime(), status: 'active'})
        CREATE (o)-[:OWNS]->(p)
        """

    query += " RETURN p.id as id"

    with driver.session() as session:
        return session.run(query, {"oid": organization_id, "id": pid, "name": name, "desc": description, "uid": owner_id}).single()["id"]

async def update_project(project_id: str, name: Optional[str], description: Optional[str]):
    driver = get_driver()
    query = "MATCH (p:Project {id: $id}) SET p.name = coalesce($name, p.name), p.description = coalesce($desc, p.description)"
    with driver.session() as session:
        session.run(query, {"id": project_id, "name": name, "desc": description})

async def archive_project(project_id: str):
    driver = get_driver()
    # Cascade: Project -> Themes -> Spaces
    query = """
    MATCH (p:Project {id: $id})
    SET p.status = 'archived'
    WITH p
    OPTIONAL MATCH (p)-[:HAS_THEME]->(t:Theme)
    SET t.status = 'archived'
    WITH t
    OPTIONAL MATCH (t)-[:HAS_SPACE]->(s:Space)
    SET s.status = 'archived'
    """
    with driver.session() as session:
        session.run(query, {"id": project_id})

async def get_project_themes(project_id: str, user_email: str) -> List[Dict]:
    driver = get_driver()
    query = """
    MATCH (org:Organization)-[:OWNS]->(p:Project {id: $pid})
    MATCH (u:User {email: toLower($email)})
    
    // Determine hierarchy roles
    OPTIONAL MATCH (u)-[r_org:HAS_ROLE]->(org)
    WITH org, p, u, coalesce(r_org.role, 'member') as org_role_direct
    
    OPTIONAL MATCH (u)-[r_proj:HAS_ROLE]->(p)
    WITH org, p, u, org_role_direct, coalesce(r_proj.role, 'member') as proj_role_direct
    
    WITH org, p, u,
         CASE 
            WHEN u.is_platform_admin = true OR org_role_direct = 'admin' OR proj_role_direct = 'admin' THEN 'admin'
            ELSE 'member'
         END as context_role
         
    MATCH (p)-[:HAS_THEME]->(t:Theme)
    WHERE t.status IS NULL OR t.status <> 'archived'
    
    // Determine effective theme role
    OPTIONAL MATCH (u)-[r_theme:HAS_ROLE]->(t)
    WITH org, p, t, u, context_role, coalesce(r_theme.role, 'member') as theme_role_direct
    
    WITH org, p, t, 
         CASE
            WHEN context_role = 'admin' THEN 'admin'
            ELSE theme_role_direct
         END as effective_role
    
    // Counting active factors/claims
    OPTIONAL MATCH (t)-[:HAS_FACTOR]->(f:Factor)
    WITH t, org, p, effective_role, count(f) as claim_count
    
    // Counting members (User -> HAS_ROLE -> Theme)
    OPTIONAL MATCH (member:User)-[:HAS_ROLE]->(t)
    WITH t, org, p, effective_role, claim_count, count(member) as member_count

    RETURN {
        id: t.id,
        name: t.name,
        description: t.description,
        project_name: p.name,
        organization_name: org.name,
        role: effective_role,
        status: t.status,
        is_archived: (t.status = 'archived' OR p.status = 'archived' OR org.status = 'archived'),
        stats: {
            active_claims: claim_count,
            members: member_count
        }
    } as theme_data
    """
    with driver.session() as session:
        return [r["theme_data"] for r in session.run(query, {"pid": project_id, "email": user_email})]

async def create_theme(project_id: str, name: str, description: Optional[str] = None, owner_id: Optional[str] = None) -> str:
    driver = get_driver()
    tid = str(uuid.uuid4())
    query = """
    MATCH (p:Project {id: $pid})
    MATCH (u:User {id: $uid}) // Ensure user exists
    CREATE (t:Theme {id: $id, name: $name, description: $desc, created_at: datetime(), status: 'active'})
    CREATE (p)-[:HAS_THEME]->(t)
    CREATE (u)-[:HAS_ROLE {role: 'admin'}]->(t)
    RETURN t.id as id
    """
    with driver.session() as session:
         return session.run(query, {"pid": project_id, "id": tid, "name": name, "desc": description, "uid": owner_id}).single()["id"]

async def update_theme(theme_id: str, name: Optional[str], description: Optional[str]):
    driver = get_driver()
    query = "MATCH (t:Theme {id: $id}) SET t.name = coalesce($name, t.name), t.description = coalesce($desc, t.description)"
    with driver.session() as session:
        session.run(query, {"id": theme_id, "name": name, "desc": description})

async def archive_theme(theme_id: str):
    driver = get_driver()
    # Cascade: Theme -> Spaces
    query = """
    MATCH (t:Theme {id: $id})
    SET t.status = 'archived'
    WITH t
    OPTIONAL MATCH (t)-[:HAS_SPACE]->(s:Space)
    SET s.status = 'archived'
    """
    with driver.session() as session:
        session.run(query, {"id": theme_id})

async def create_space(theme_id: str, name: str, description: Optional[str] = None, owner_id: Optional[str] = None) -> str:
    driver = get_driver()
    sid = str(uuid.uuid4())
    query = """
    MATCH (t:Theme {id: $tid})
    MATCH (u:User {id: $uid})
    CREATE (s:Space {id: $id, name: $name, description: $desc, created_at: datetime(), status: 'active'})
    CREATE (t)-[:HAS_SPACE]->(s)
    CREATE (u)-[:HAS_ROLE {role: 'admin'}]->(s)
    RETURN s.id as id
    """
    with driver.session() as session:
         return session.run(query, {"tid": theme_id, "id": sid, "name": name, "desc": description, "uid": owner_id}).single()["id"]

async def update_space(space_id: str, name: Optional[str], description: Optional[str]):
    driver = get_driver()
    query = "MATCH (s:Space {id: $id}) SET s.name = coalesce($name, s.name), s.description = coalesce($desc, s.description)"
    with driver.session() as session:
        session.run(query, {"id": space_id, "name": name, "desc": description})

async def archive_space(space_id: str):
    driver = get_driver()
    query = "MATCH (s:Space {id: $id}) SET s.status = 'archived'"
    with driver.session() as session:
        session.run(query, {"id": space_id})

async def get_spaces_by_theme(theme_id: str, user_id: str) -> List[Dict]:
    driver = get_driver()
    logger.info(f"DEBUG: get_spaces_by_theme called with theme_id={theme_id}, user_id={user_id}")
    query = """
    MATCH (org:Organization)-[:OWNS]->(p:Project)-[:HAS_THEME]->(t:Theme {id: $tid})
    MATCH (t)-[:HAS_SPACE]->(s:Space)
    MATCH (u:User {id: $uid})
    
    // Simplified: Strict Explicit Membership. No inheritance.
    // User must have a direct HAS_ROLE relationship with the Space.
    
    MATCH (u)-[r_space:HAS_ROLE]->(s)
         
    RETURN {
        id: s.id,
        name: s.name,
        description: s.description,
        status: s.status,
        is_archived: (s.status = 'archived' OR t.status = 'archived' OR p.status = 'archived' OR org.status = 'archived'),
        role: r_space.role,
        created_at: toString(s.created_at)
    } as space_data
    """
    with driver.session() as session:
        return [r["space_data"] for r in session.run(query, {"tid": theme_id, "uid": user_id})]

async def get_space(space_id: str, user_id: str) -> Optional[Dict]:
    driver = get_driver()
    query = """
    MATCH (org:Organization)-[:OWNS]->(p:Project)-[:HAS_THEME]->(t:Theme)-[:HAS_SPACE]->(s:Space {id: $sid})
    MATCH (u:User {id: $uid})
    
    // Simplified: Strict Explicit Membership.
    MATCH (u)-[r_space:HAS_ROLE]->(s)
    
    RETURN {
        id: s.id,
        name: s.name,
        description: s.description,
        status: s.status,
        is_archived: (s.status = 'archived' OR t.status = 'archived' OR p.status = 'archived' OR org.status = 'archived'),
        theme_id: t.id,
        theme_name: t.name,
        project_id: p.id,
        project_name: p.name,
        organization_id: org.id,
        organization_name: org.name,
        role: r_space.role, 
        created_at: toString(s.created_at)
    } as space_data
    """
    with driver.session() as session:
        result = session.run(query, {"sid": space_id, "uid": user_id})
        record = result.single()
        return record["space_data"] if record else None

# --- Space Members ---

async def get_space_users(space_id: str) -> List[Dict]:
     driver = get_driver()
     query = "MATCH (s:Space {id: $sid})<-[r:HAS_ROLE]-(u:User) RETURN u, r.role as role"
     with driver.session() as session:
         return [{"id": rec["u"]["id"], "name": rec["u"].get("name",""), "email": rec["u"]["email"], "role": rec["role"]} for rec in session.run(query, {"sid": space_id})]

async def add_user_to_space(email: str, space_id: str, role: str):
    await create_user(email)
    driver = get_driver()
    query = """
    MATCH (u:User {email: toLower($email)})
    MATCH (s:Space {id: $sid})
    MERGE (u)-[r:HAS_ROLE]->(s)
    SET r.role = $role, r.updated_at = datetime()
    """
    with driver.session() as session:
        session.run(query, {"email": email, "sid": space_id, "role": role})

async def update_space_member_role(space_id: str, user_id: str, role: str):
     driver = get_driver()
     query = """
     MATCH (s:Space {id: $sid})<-[r:HAS_ROLE]-(u:User {id: $uid})
     SET r.role = $role, r.updated_at = datetime()
     """
     with driver.session() as session:
         session.run(query, {"sid": space_id, "uid": user_id, "role": role})

async def delete_space_member(space_id: str, user_id: str):
     driver = get_driver()
     query = """
     MATCH (s:Space {id: $sid})<-[r:HAS_ROLE]-(u:User {id: $uid})
     DELETE r
     """
     with driver.session() as session:
         session.run(query, {"sid": space_id, "uid": user_id})


async def get_project_id_by_theme(theme_id: str) -> Optional[str]:
    driver = get_driver()
    query = "MATCH (p:Project)-[:HAS_THEME]->(t:Theme {id: $tid}) RETURN p.id as pid"
    try:
        with driver.session() as session:
            result = session.run(query, {"tid": theme_id})
            record = result.single()
            return record["pid"] if record else None
    except Exception as e:
        logger.error(f"Error resolving project for theme {theme_id}: {e}")
        return None

async def get_project_id_by_factor(factor_id: str) -> Optional[str]:
    driver = get_driver()
    query = """
    MATCH (p:Project)-[:HAS_THEME]->(t:Theme)-[:HAS_FACTOR]->(f:Factor {id: $fid})
    RETURN p.id as pid
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"fid": factor_id})
            record = result.single()
            return record["pid"] if record else None
    except Exception as e:
        logger.error(f"Error resolving project for factor {factor_id}: {e}")
        return None

async def get_project_id_by_claim(claim_id: str) -> Optional[str]:
    driver = get_driver()
    # Claim linked to Factor linked to Theme linked to Project
    # Or Claim linked to Theme directly (via GENERATED)?
    # Manual claims might not be directly linked to theme except via factors?
    # Actually create_claim_manual links factors to Theme.
    # Let's traverse via Source Factor -> Theme -> Project
    query = """
    MATCH (p:Project)-[:HAS_THEME]->(t:Theme)-[:HAS_FACTOR]->(f:Factor)-[:CLAIMS]->(c:Claim {id: $cid})
    RETURN p.id as pid
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"cid": claim_id})
            record = result.single()
            return record["pid"] if record else None
    except Exception as e:
        logger.error(f"Error resolving project for claim {claim_id}: {e}")
        return None
        
async def update_organization(org_id: str, name: Optional[str], description: Optional[str]):
    driver = get_driver()
    query = "MATCH (o:Organization {id: $id}) SET o.name = coalesce($name, o.name), o.description = coalesce($desc, o.description)"
    with driver.session() as session:
        session.run(query, {"id": org_id, "name": name, "desc": description})

async def archive_organization(org_id: str):
    driver = get_driver()
    query = "MATCH (o:Organization {id: $id}) SET o.status = 'archived'"
    with driver.session() as session:
        session.run(query, {"id": org_id})

# --- Claims / Factors / Manual Editing ---

async def get_claims_for_theme(theme_id: str) -> List[Claim]:
    driver = get_driver()
    # Path 1: Claims generated by conversations linked to this theme
    # Path 2: Claims between factors that are both associated with this theme (manual claims)
    query = """
    MATCH (th:Theme {id: $tid})
    
    // Path 1: Conversation-based
    OPTIONAL MATCH (th)<-[:BELONGS_TO]-(t:ConversationThread)-[:GENERATED]->(c_path1:Claim)
    MATCH (s1:Factor)-[:CLAIMS]->(c_path1)-[:TO]->(t_node1:Factor)
    OPTIONAL MATCH (th)-[rs1:HAS_FACTOR]->(s1)
    OPTIONAL MATCH (th)-[rt1:HAS_FACTOR]->(t_node1)
    WITH th, collect({
        node: c_path1,
        source: s1.name, source_id: s1.id, s_type: rs1.role,
        target: t_node1.name, target_id: t_node1.id, t_type: rt1.role
    }) as claims_list1
    
    // Path 2: Direct Factor connections (covers manual claims)
    OPTIONAL MATCH (th)-[:HAS_FACTOR]->(s2:Factor)-[:CLAIMS]->(c_path2:Claim)-[:TO]->(t_node2:Factor)
    WHERE (th)-[:HAS_FACTOR]->(t_node2)
    OPTIONAL MATCH (th)-[rs2:HAS_FACTOR]->(s2)
    OPTIONAL MATCH (th)-[rt2:HAS_FACTOR]->(t_node2)
    WITH claims_list1, collect({
        node: c_path2,
        source: s2.name, source_id: s2.id, s_type: rs2.role,
        target: t_node2.name, target_id: t_node2.id, t_type: rt2.role
    }) as claims_list2
    
    UNWIND (claims_list1 + claims_list2) as item
    WITH item WHERE item.node IS NOT NULL
    RETURN DISTINCT item.node as c, item.source as source, item.source_id as source_id, item.s_type as s_type,
                    item.target as target, item.target_id as target_id, item.t_type as t_type
    """
    
    try:
        with driver.session() as session:
            result = session.run(query, {"tid": theme_id})
            claims = []
            for record in result:
                node = record["c"]
                claim_data = dict(node)
                claim_data['source_node'] = record["source"]
                claim_data['source_id'] = record["source_id"]
                claim_data['source_type'] = record["s_type"] or "systeemelement"
                claim_data['target_node'] = record["target"]
                claim_data['target_id'] = record["target_id"]
                claim_data['target_type'] = record["t_type"] or "systeemelement"
                
                # Convert neo4j datetime to string for Pydantic if necessary
                if 'created_at' in claim_data and hasattr(claim_data['created_at'], 'isoformat'):
                    claim_data['created_at'] = claim_data['created_at'].isoformat()
                
                # Final safeguard: ensure ID is string
                if 'id' in claim_data:
                    claim_data['id'] = str(claim_data['id'])
                
                try:
                    claims.append(Claim(**claim_data))
                except Exception as ve:
                    logger.warning(f"Skipping invalid claim {claim_data.get('id')}: {ve}")
                    
            return claims
    except Exception as e:
        logger.error(f"Failed to fetch theme claims: {e}")
        return []

async def get_factors_for_theme(theme_id: str) -> List[Dict]:
    driver = get_driver()
    query = """
    MATCH (t:Theme {id: $tid})-[:HAS_FACTOR]->(f:Factor)
    RETURN f
    """
    with driver.session() as session:
        return [dict(r["f"]) for r in session.run(query, {"tid": theme_id})]

async def create_factor_manual(name: str, description: Optional[str], type: str, theme_id: Optional[str]) -> str:
    driver = get_driver()
    fid = str(uuid.uuid4())
    query = """
    CREATE (f:Factor {id: $id, name: $name, description: $desc, type: $type, created_at: datetime()})
    """
    if theme_id:
        query += """
        WITH f
        MATCH (t:Theme {id: $tid})
        MERGE (t)-[:HAS_FACTOR]->(f)
        """
        
    query += " RETURN f.id as id"
    
    with driver.session() as session:
        return session.run(query, {"id": fid, "name": name, "desc": description, "type": type, "tid": theme_id}).single()["id"]

async def update_factor_manual(factor_id: str, name: Optional[str], description: Optional[str], type: Optional[str], theme_id: Optional[str]):
    driver = get_driver()
    query = """
    MATCH (f:Factor {id: $id})
    SET f.name = coalesce($name, f.name), 
        f.description = coalesce($desc, f.description),
        f.type = coalesce($type, f.type)
    """
    with driver.session() as session:
        session.run(query, {"id": factor_id, "name": name, "desc": description, "type": type})

async def delete_factor_manual(factor_id: str):
    driver = get_driver()
    query = "MATCH (f:Factor {id: $id}) DETACH DELETE f"
    with driver.session() as session:
        session.run(query, {"id": factor_id})

async def create_claim_manual(theme_id: str, source_id: str, target_id: str, statement: str, polarity: str = "+", confidence: float = 1.0):
    driver = get_driver()
    cid = str(uuid.uuid4())
    query = """
    MATCH (s:Factor {id: $sid}), (t:Factor {id: $tid})
    MATCH (theme:Theme {id: $thid})
    MERGE (c:Claim {id: $cid})
    SET c.statement = $stmt, 
        c.polarity = $pol, 
        c.confidence = $conf, 
        c.relationship_type = 'CAUSES',
        c.created_at = datetime()
        
    MERGE (s)-[:CLAIMS]->(c)
    MERGE (c)-[:TO]->(t)
    
    // Ensure factors are linked to theme
    MERGE (theme)-[:HAS_FACTOR]->(s)
    MERGE (theme)-[:HAS_FACTOR]->(t)
    """
    query += " RETURN c.id as id"
    with driver.session() as session:
        return session.run(query, {"cid": cid, "sid": source_id, "tid": target_id, "stmt": statement, "pol": polarity, "conf": confidence, "thid": theme_id}).single()["id"]

async def update_claim_manual(claim_id: str, statement: Optional[str], polarity: Optional[str], confidence: Optional[float], source_id: Optional[str], target_id: Optional[str]):
    driver = get_driver()
    query = """
    MATCH (c:Claim {id: $id})
    SET c.statement = coalesce($stmt, c.statement),
        c.polarity = coalesce($pol, c.polarity),
        c.confidence = coalesce($conf, c.confidence)
    """
    with driver.session() as session:
        session.run(query, {"id": claim_id, "stmt": statement, "pol": polarity, "conf": confidence})

async def delete_claim_manual(claim_id: str):
    driver = get_driver()
    query = "MATCH (c:Claim {id: $id}) DETACH DELETE c"
    with driver.session() as session:
        session.run(query, {"id": claim_id})

async def create_conversation_thread(space_id: str, topic: str) -> str:
    driver = get_driver()
    tid = str(uuid.uuid4())
    query = """
    MATCH (s:Space {id: $sid})
    CREATE (t:ConversationThread {id: $id, topic: $topic, status: 'active', created_at: datetime()})
    CREATE (s)-[:HAS_THREAD]->(t)
    RETURN t.id as id
    """
    with driver.session() as session:
        return session.run(query, {"sid": space_id, "id": tid, "topic": topic}).single()["id"]

async def get_threads_by_space(space_id: str) -> List[Dict]:
    driver = get_driver()
    query = """
    MATCH (s:Space {id: $sid})-[:HAS_THREAD]->(t:ConversationThread)
    RETURN {
        id: t.id,
        topic: t.topic,
        status: t.status,
        created_at: toString(t.created_at)
    } as thread_data
    """
    with driver.session() as session:
        return [r["thread_data"] for r in session.run(query, {"sid": space_id})]
