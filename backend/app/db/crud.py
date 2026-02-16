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
    Updated for Base/Version Refactor:
    - Creates FactorBase/FactorVersion if not exist.
    - Creates ClaimBase/ClaimVersion.
    - Uses active ThemeVersion.
    """
    driver = get_driver()
    query = """
    MERGE (ct:ConversationThread {id: $cid})
    WITH ct, ct.space_id as version_id 
    
    // Ensure we have an active ThemeVersion to attach to
    MATCH (v:ThemeVersion {id: version_id})
    WHERE v.status = 'active'
    
    UNWIND $claims as claim
    
    // --- Source Factor ---
    // Try to find existing active FactorVersion by name within this ThemeVersion
    OPTIONAL MATCH (v)-[:HAS_FACTOR]->(existing_fv_source:FactorVersion {name: claim.source_node})
    WITH ct, v, claim, existing_fv_source
    
    CALL {
        WITH v, claim, existing_fv_source
        // IF existing found, use it. ELSE create new Base + Version
        WHERE existing_fv_source IS NULL
        CREATE (fb_source:FactorBase {
            id: randomUUID(),
            created_at: datetime(),
            created_by: 'system_agent' // Agent doesn't have ID yet?
        })
        CREATE (fv_source:FactorVersion {
            id: randomUUID(),
            base_id: fb_source.id,
            name: claim.source_node,
            type: coalesce(claim.source_type, 'systeemelement'),
            version_id: v.id,
            created_at: datetime()
        })
        CREATE (v)-[:HAS_FACTOR]->(fv_source)
        // No User-Created ink for agent? Or link to System Admin?
        RETURN fv_source as source_v
        
        UNION
        
        WITH existing_fv_source
        WHERE existing_fv_source IS NOT NULL
        RETURN existing_fv_source as source_v
    }
    
    // --- Target Factor (Same logic) ---
    WITH ct, v, claim, source_v
    OPTIONAL MATCH (v)-[:HAS_FACTOR]->(existing_fv_target:FactorVersion {name: claim.target_node})
    
    CALL {
        WITH v, claim, existing_fv_target
        WHERE existing_fv_target IS NULL
        CREATE (fb_target:FactorBase {
            id: randomUUID(),
            created_at: datetime(),
            created_by: 'system_agent'
        })
        CREATE (fv_target:FactorVersion {
            id: randomUUID(),
            base_id: fb_target.id,
            name: claim.target_node,
            type: coalesce(claim.target_type, 'systeemelement'),
            version_id: v.id,
            created_at: datetime()
        })
        CREATE (v)-[:HAS_FACTOR]->(fv_target)
        RETURN fv_target as target_v
        
        UNION
        
        WITH existing_fv_target
        WHERE existing_fv_target IS NOT NULL
        RETURN existing_fv_target as target_v
    }
    
    // --- Claim ---
    CREATE (cb:ClaimBase {
        id: coalesce(claim.id, randomUUID()),
        created_at: datetime(),
        created_by: 'system_agent'
    })
    CREATE (cv:ClaimVersion {
        id: randomUUID(),
        base_id: cb.id,
        statement: claim.statement,
        confidence: claim.confidence,
        polarity: claim.polarity,
        source_version_id: source_v.id,
        target_version_id: target_v.id,
        created_at: datetime()
    })
    
    // Link ClaimVersion to FactorVersions
    CREATE (source_v)-[:CLAIMS]->(cv)
    CREATE (cv)-[:TO]->(target_v)
    
    // Link to Conversation
    MERGE (ct)-[:GENERATED]->(cv)
    """
    
    # Note: Logic above is simplified "Merge if not exists" using CALL/UNION
    # Agent logic is complex. For now focusing on manual endpoints.
    # Placeholder for Agent logic update until verified.
    pass

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
    MATCH (c:ConversationThread {id: $cid})-[:GENERATED]->(cl:ClaimVersion)
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
    MATCH (c:ConversationThread {id: $cid})-[rel:GENERATED]->(cl:ClaimVersion)
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
    MATCH (u:User {id: $author_id})
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
        where_clauses.append("u.id = $author_id")
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

async def get_user_organizations(user_id: str) -> List[Dict]:
    """Returns orgs for a specific user."""
    driver = get_driver()
    query = """
    MATCH (u:User {id: $uid})
    MATCH (u)-[:HAS_ROLE]->(o:Organization)
    WHERE o.status IS NULL OR o.status <> 'archived'
    RETURN o
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"uid": user_id})
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
     query = "MATCH (t:ThemeBase {id: $tid})<-[r:HAS_ROLE]-(u:User) RETURN u, r.role as role"
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
    OPTIONAL MATCH (p)-[:HAS_THEME]->(t:ThemeBase)
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
    OPTIONAL MATCH (p)-[:HAS_THEME]->(t:ThemeBase)
    SET t.status = 'archived'
    WITH t
    OPTIONAL MATCH (t)-[:HAS_VERSION]->(s:ThemeVersion)
    SET s.status = 'archived'
    """
    with driver.session() as session:
        session.run(query, {"id": project_id})

async def get_project_themes(project_id: str, user_id: str) -> List[Dict]:
    driver = get_driver()
    query = """
    MATCH (org:Organization)-[:OWNS]->(p:Project {id: $pid})
    MATCH (u:User {id: $uid})
    
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
         
    MATCH (p)-[:HAS_THEME]->(t:ThemeBase)
    WHERE t.status IS NULL OR t.status <> 'archived'
    
    // Determine effective theme role
    OPTIONAL MATCH (u)-[r_theme:HAS_ROLE]->(t)
    WITH org, p, t, u, context_role, coalesce(r_theme.role, 'member') as theme_role_direct
    
    WITH org, p, t, 
         CASE
            WHEN context_role = 'admin' THEN 'admin'
            ELSE theme_role_direct
         END as effective_role
    
    // Fetch Active Version for Metadata and Stats
    OPTIONAL MATCH (t)-[:HAS_ACTIVE_VERSION]->(av:ThemeVersion)
    
    // Counting active factors/claims
    OPTIONAL MATCH (av)-[:HAS_FACTOR]->(f:FactorVersion)
    WITH t, org, p, av, effective_role, count(f) as claim_count
    
    // Counting members (User -> HAS_ROLE -> Theme)
    OPTIONAL MATCH (member:User)-[:HAS_ROLE]->(t)
    WITH t, org, p, av, effective_role, claim_count, count(member) as member_count

    RETURN {
        id: t.id,
        name: av.name,
        description: av.description,
        project_name: p.name,
        organization_name: org.name,
        organization_id: org.id,
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
        return [r["theme_data"] for r in session.run(query, {"pid": project_id, "uid": user_id})]

async def create_theme(project_id: str, name: str, description: Optional[str] = None, owner_id: Optional[str] = None) -> str:
    driver = get_driver()
    tid = str(uuid.uuid4())
    vid = str(uuid.uuid4())
    query = """
    MATCH (p:Project {id: $pid})
    MATCH (u:User {id: $uid})
    
    // 1. Create Base (Identity)
    CREATE (t:Theme:ThemeBase {
        id: $id, 
        created_at: datetime(), 
        created_by: $uid
    })
    CREATE (p)-[:HAS_THEME]->(t)
    CREATE (u)-[:CREATED]->(t) // Immutable Authorship
    CREATE (u)-[:HAS_ROLE {role: 'admin'}]->(t)
    
    // 2. Initialize V1 (State)
    CREATE (v:ThemeVersion {
        id: $vid,
        base_id: $id,
        name: $name, // V1 name usually matches Base name initially
        description: $desc,
        status: 'active',
        created_at: datetime(),
        valid_from: datetime(),
        valid_to: NULL
    })
    CREATE (t)-[:HAS_VERSION]->(v)
    CREATE (t)-[:HAS_ACTIVE_VERSION]->(v)
    CREATE (u)-[:HAS_ROLE {role: 'admin'}]->(v) // Strict Access: Creator gets role on V1
    
    RETURN t.id as id
    """
    with driver.session() as session:
         return session.run(query, {"pid": project_id, "id": tid, "vid": vid, "name": name, "desc": description, "uid": owner_id}).single()["id"]



async def update_theme(theme_id: str, name: Optional[str], description: Optional[str]):
    driver = get_driver()
    query = "MATCH (t:ThemeBase {id: $id}) SET t.name = coalesce($name, t.name), t.description = coalesce($desc, t.description)"
    with driver.session() as session:
        session.run(query, {"id": theme_id, "name": name, "desc": description})

async def archive_theme(theme_id: str):
    driver = get_driver()
    # Cascade: Theme -> Spaces
    query = """
    MATCH (t:ThemeBase {id: $id})
    SET t.status = 'archived'
    WITH t
    OPTIONAL MATCH (t)-[:HAS_VERSION]->(s:ThemeVersion)
    SET s.status = 'archived'
    """
    with driver.session() as session:
        session.run(query, {"id": theme_id})

async def create_theme_version(theme_id: str, name: str, description: Optional[str] = None, owner_id: Optional[str] = None) -> str:
    driver = get_driver()
    sid = str(uuid.uuid4())
    query = """
    MATCH (t:ThemeBase {id: $tid})
    MATCH (u:User {id: $uid})
    CREATE (s:ThemeVersion {
        id: $id, 
        name: $name, 
        description: $desc, 
        created_at: datetime(), 
        status: 'active',
        valid_from: datetime(),
        valid_to: NULL
    })
    CREATE (t)-[:HAS_VERSION]->(s)
    CREATE (u)-[:HAS_ROLE {role: 'admin'}]->(s)
    RETURN s.id as id
    """
    with driver.session() as session:
         return session.run(query, {"tid": theme_id, "id": sid, "name": name, "desc": description, "uid": owner_id}).single()["id"]

async def update_theme_version(version_id: str, name: Optional[str], description: Optional[str]):
    driver = get_driver()
    query = "MATCH (s:ThemeVersion {id: $id}) SET s.name = coalesce($name, s.name), s.description = coalesce($desc, s.description)"
    with driver.session() as session:
        session.run(query, {"id": version_id, "name": name, "desc": description})

async def archive_theme_version(version_id: str):
    driver = get_driver()
    query = "MATCH (s:ThemeVersion {id: $id}) SET s.status = 'archived'"
    with driver.session() as session:
        session.run(query, {"id": version_id})

async def get_theme_by_id_simple(theme_id: str) -> Dict[str, Any]:
    """
    Fetches basic theme data (name, description) by ID.
    Used for notifications/logging where full hierarchy isn't needed.
    """
    driver = get_driver()
    query = """
    MATCH (t:ThemeBase {id: $tid})-[:HAS_ACTIVE_VERSION]->(v:ThemeVersion)
    RETURN t.id as id, v.name as name, v.description as description
    """
    try:
        with driver.session() as session:
            record = session.run(query, {"tid": theme_id}).single()
            if record:
                return dict(record)
            return {}
    except Exception as e:
        logger.error(f"Error fetching theme simple: {e}")
        return {}

async def get_theme_versions_by_theme(theme_id: str, user_id: str) -> List[Dict]:
    driver = get_driver()
    logger.info(f"DEBUG: get_theme_versions_by_theme called with theme_id={theme_id}, user_id={user_id}")
    query = """
    MATCH (org:Organization)-[:OWNS]->(p:Project)-[:HAS_THEME]->(t:ThemeBase {id: $tid})
    MATCH (t)-[:HAS_VERSION]->(s:ThemeVersion)
    MATCH (u:User {id: $uid})
    
    // Check for explicit membership on the Theme Base (t)
    // We assume if you have access to the Theme, you can see its history.
    MATCH (u)-[r_space:HAS_ROLE]->(t)
         
    
    OPTIONAL MATCH (s)-[:HAS_SESSION]->(sess:VotingSession)
    WHERE sess.status = 'active'
    
    OPTIONAL MATCH (s)-[:DERIVED_FROM]->(parent:ThemeVersion)
         
    RETURN {
        id: s.id,
        name: s.name,
        description: s.description,
        status: CASE WHEN sess IS NOT NULL THEN 'voting' ELSE s.status END,
        is_archived: (s.status = 'archived' OR t.status = 'archived' OR p.status = 'archived' OR org.status = 'archived'),
        role: r_space.role,
        created_at: toString(s.created_at),
        valid_from: toString(s.valid_from),
        valid_to: toString(s.valid_to),
        derived_from_id: parent.id
    } as version_data
    """
    with driver.session() as session:
        return [r["version_data"] for r in session.run(query, {"tid": theme_id, "uid": user_id})]

async def get_theme_version(version_id: str, user_id: str) -> Optional[Dict]:
    driver = get_driver()
    query = """
    MATCH (org:Organization)-[:OWNS]->(p:Project)-[:HAS_THEME]->(t:ThemeBase)-[:HAS_VERSION]->(s:ThemeVersion {id: $sid})
    MATCH (u:User {id: $uid})
    
    // Simplified: Strict Explicit Membership.
    MATCH (u)-[r_space:HAS_ROLE]->(s)
    
    // Check for active voting session to override status
    OPTIONAL MATCH (s)-[:HAS_SESSION]->(sess:VotingSession)
    WHERE sess.status = 'active'
    
    RETURN {
        id: s.id,
        name: s.name,
        description: s.description,
        status: CASE WHEN sess IS NOT NULL THEN 'voting' ELSE s.status END,
        is_archived: (s.status = 'archived' OR t.status = 'archived' OR p.status = 'archived' OR org.status = 'archived'),
        theme_id: t.id,
        theme_name: t.name,
        project_id: p.id,
        project_name: p.name,
        organization_id: org.id,
        organization_name: org.name,
        role: r_space.role, 
        created_at: toString(s.created_at),
        valid_from: toString(s.valid_from),
        valid_to: toString(s.valid_to)
    } as version_data
    """
    with driver.session() as session:
        result = session.run(query, {"sid": version_id, "uid": user_id})
        record = result.single()
        return record["version_data"] if record else None

async def get_theme_active_version(theme_id: str, user_id: str) -> Optional[Dict]:
    """
    Get the currently active version (valid_to IS NULL) for a theme.
    Returns None if no active version exists or user has no access.
    """
    driver = get_driver()
    query = """
    MATCH (org:Organization)-[:OWNS]->(p:Project)-[:HAS_THEME]->(t:ThemeBase {id: $tid})
    MATCH (t)-[:HAS_VERSION]->(s:ThemeVersion)
    WHERE s.valid_to IS NULL
    
    // Check for active voting session to override status
    OPTIONAL MATCH (s)-[:HAS_SESSION]->(sess:VotingSession)
    WHERE sess.status = 'active'
    
    MATCH (u:User {id: $uid})
    
    // Simplified: Strict Explicit Membership.
    // Check Permissions (Hierarchical)
    // 1. Direct Version Role
    OPTIONAL MATCH (u)-[r_ver:HAS_ROLE]->(s)
    // 2. Theme Role
    OPTIONAL MATCH (u)-[r_theme:HAS_ROLE]->(t)
    // 3. Project Role
    OPTIONAL MATCH (u)-[r_proj:HAS_ROLE]->(p)
    // 4. Org Role
    OPTIONAL MATCH (u)-[r_org:HAS_ROLE]->(org)
    
    // Ensure at least one access path or platform admin
    WHERE r_ver IS NOT NULL OR r_theme IS NOT NULL OR r_proj IS NOT NULL OR r_org IS NOT NULL OR u.is_platform_admin = true
    
    RETURN {
        id: s.id,
        name: s.name,
        description: s.description,
        status: CASE WHEN sess IS NOT NULL THEN 'voting' ELSE s.status END,
        is_archived: (s.status = 'archived' OR t.status = 'archived' OR p.status = 'archived' OR org.status = 'archived'),
        theme_id: t.id,
        theme_name: s.name,
        project_id: p.id,
        project_name: p.name,
        organization_id: org.id,
        organization_name: org.name,
        // Calculate highest effective role
        role: coalesce(r_ver.role, r_theme.role, r_proj.role, r_org.role, CASE WHEN u.is_platform_admin THEN 'admin' ELSE 'member' END), 
        created_at: toString(s.created_at),
        valid_from: toString(s.valid_from),
        valid_to: toString(s.valid_to)
    } as version_data
    """
    with driver.session() as session:
        result = session.run(query, {"tid": theme_id, "uid": user_id})
        record = result.single()
        return record["version_data"] if record else None

# --- ThemeVersion Members ---

async def get_active_version_id_if_theme(entity_id: str) -> str:
    """
    Checks if the entity_id belongs to a ThemeBase.
    If so, returns the ID of the currently ACTIVE ThemeVersion.
    If not, returns the entity_id as-is (e.g. Organization or Project ID, or already a Version ID).
    """
    driver = get_driver()
    query = """
    MATCH (t:ThemeBase {id: $id})
    OPTIONAL MATCH (t)-[:HAS_ACTIVE_VERSION]->(v:ThemeVersion)
    RETURN t.id as theme_id, v.id as version_id
    """
    with driver.session() as session:
        result = session.run(query, {"id": entity_id}).single()
        if result and result["theme_id"]:
            if result["version_id"]:
                logger.info(f"Redirecting Invite: Theme {entity_id} -> Active Version {result['version_id']}")
                return result["version_id"]
            else:
                 # Theme exists but no active version? Should rare.
                 # Fallback to Theme ID? Or Error?
                 # If we return Theme ID, it fails strict check later.
                 logger.warning(f"Invite target is Theme {entity_id} but no active version found. Invite may fail strict checks.")
                 return entity_id
        return entity_id

async def get_theme_version_users(version_id: str) -> List[Dict]:
     driver = get_driver()
     query = "MATCH (s:ThemeVersion {id: $sid})<-[r:HAS_ROLE]-(u:User) RETURN u, r.role as role"
     with driver.session() as session:
         return [{"id": rec["u"]["id"], "name": rec["u"].get("name",""), "email": rec["u"]["email"], "role": rec["role"]} for rec in session.run(query, {"sid": version_id})]

async def add_user_to_theme_version(email: str, version_id: str, role: str):
    await create_user(email)
    driver = get_driver()
    query = """
    MATCH (u:User {email: toLower($email)})
    MATCH (s:ThemeVersion {id: $sid})
    MERGE (u)-[r:HAS_ROLE]->(s)
    SET r.role = $role, r.updated_at = datetime()
    """
    with driver.session() as session:
        session.run(query, {"email": email, "sid": version_id, "role": role})

async def update_theme_version_member_role(version_id: str, user_id: str, role: str):
     driver = get_driver()
     query = """
     MATCH (s:ThemeVersion {id: $sid})<-[r:HAS_ROLE]-(u:User {id: $uid})
     SET r.role = $role, r.updated_at = datetime()
     """
     with driver.session() as session:
         session.run(query, {"sid": version_id, "uid": user_id, "role": role})

async def delete_theme_version_member(version_id: str, user_id: str):
     driver = get_driver()
     query = """
     MATCH (s:ThemeVersion {id: $sid})<-[r:HAS_ROLE]-(u:User {id: $uid})
     DELETE r
     """
     with driver.session() as session:
         session.run(query, {"sid": version_id, "uid": user_id})


async def get_project_id_by_theme(theme_id: str) -> Optional[str]:
    driver = get_driver()
    query = "MATCH (p:Project)-[:HAS_THEME]->(t:ThemeBase {id: $tid}) RETURN p.id as pid"
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
    MATCH (p:Project)-[:HAS_THEME]->(t)-[:HAS_FACTOR]->(f)
    WHERE f.id = $fid
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
    query = """
    MATCH (p:Project)-[:HAS_THEME]->(t)-[:HAS_VERSION]->(tv)-[:HAS_FACTOR]->(fv)-[:CLAIMS]->(cv)<-[:HAS_VERSION]-(cb:ClaimBase {id: $id})
    RETURN p.id as pid
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"id": claim_id})
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


async def get_claims_for_version(version_id: str) -> List[Claim]:
    """
    Get all ClaimVersions visible in this ThemeVersion.
    Traverses: ThemeVersion -> FactorVersions -> Claims
    """
    driver = get_driver()
    query = """
    MATCH (tv:ThemeVersion {id: $vid})
    MATCH (tv)-[:HAS_FACTOR]->(fv_source:FactorVersion)
    MATCH (fv_source)-[rel:CLAIMS]->(cv:ClaimVersion)-[:TO]->(fv_target:FactorVersion)
    MATCH (cb:ClaimBase)-[:HAS_VERSION]->(cv) // Retrieve Base for immutable props
    
    // Optional threads for claim, source and target
    OPTIONAL MATCH (cv)-[:HAS_THREAD]->(t_claim:ConversationThread)
    OPTIONAL MATCH (fv_source)-[:HAS_THREAD]->(t_source:ConversationThread)
    OPTIONAL MATCH (fv_target)-[:HAS_THREAD]->(t_target:ConversationThread)
    
    // Ensure target is also in this version (Consistency Check)
    WHERE (tv)-[:HAS_FACTOR]->(fv_target)
    
    RETURN DISTINCT {
        id: cv.base_id,          // Identity
        version_id: cv.id,       // State
        statement: cv.statement,
        polarity: cv.polarity,
        confidence: cv.confidence,
        status: cv.status,
        
        source_id: fv_source.base_id,
        target_id: fv_target.base_id,
        source_version_id: fv_source.id,
        target_version_id: fv_target.id,
        
        claim_thread_id: t_claim.id,
        source_thread_id: t_source.id,
        target_thread_id: t_target.id,
        
        created_at: toString(cv.created_at),
        created_by: cb.created_by  // Immutable Creator
    } as claim
    """
    
    with driver.session() as session:
        results = session.run(query, {"vid": version_id})
        claims = []
        for record in results:
            c = record["claim"]
            # Map complexity if any
            try:
                claims.append(Claim(**c))
            except Exception as e:
                logger.warning(f"Invalid claim data for {c.get('id')}: {e}")
        return claims

async def get_claims_for_theme(theme_id: str) -> List[Claim]:
    """
    Legacy/Active Wrapper: Get claims for the ACTIVE ThemeVersion.
    """
    driver = get_driver()
    query = """
    MATCH (t:ThemeBase {id: $tid})-[:HAS_VERSION]->(tv:ThemeVersion)
    WHERE tv.status = 'active' AND tv.valid_to IS NULL
    RETURN tv.id as vid
    """
    with driver.session() as session:
        result = session.run(query, {"tid": theme_id}).single()
        if result:
            return await get_claims_for_version(result["vid"])
        return []


async def get_factors_for_version(version_id: str) -> List[Dict]:
    """
    Get all FactorVersions associated with a specific ThemeVersion.
    Returns list of dicts formatted for API response (using Base ID as 'id').
    """
    driver = get_driver()
    query = """
    MATCH (tv:ThemeVersion {id: $vid})
    MATCH (tv)-[:HAS_FACTOR]->(fv:FactorVersion)
    OPTIONAL MATCH (fv)-[:HAS_THREAD]->(t:ConversationThread)
    RETURN DISTINCT {
        id: fv.base_id,              // Frontend expects Identity ID
        version_id: fv.id,           // Specific Version ID
        name: fv.name,
        description: fv.description,
        type: fv.type,
        theme_id: fv.theme_id,       // If encoded in FactorVersion, or we omit
        thread_id: t.id
    } as factor
    """
    with driver.session() as session:
        return [r["factor"] for r in session.run(query, {"vid": version_id})]

async def get_factors_for_theme(theme_id: str) -> List[Dict]:
    """
    Legacy/Active Wrapper: Get factors for the ACTIVE ThemeVersion.
    """
    # We need to find the active version first.
    # We can do this in one query or reuse helper if we had user_id.
    # Since this is a public/general getter, we assume "System/Public" view unless user_id provided.
    # For now, let's query the active version directly.
    driver = get_driver()
    query = """
    MATCH (t:ThemeBase {id: $tid})-[:HAS_VERSION]->(tv:ThemeVersion)
    WHERE tv.status = 'active' AND tv.valid_to IS NULL
    RETURN tv.id as vid
    """
    with driver.session() as session:
        result = session.run(query, {"tid": theme_id}).single()
        if result:
            return await get_factors_for_version(result["vid"])
        return []


async def create_factor_manual(name: str, description: Optional[str], type: str, theme_id: str, author_id: str) -> str:
    """
    Creates a FactorBase + FactorVersion.
    Links Base to User (Author).
    Links Version to Active ThemeVersion.
    Note: Requires theme_id (to find active version) and author_id (for Immutable Authorship).
    """
    driver = get_driver()
    fid = str(uuid.uuid4())
    vid = str(uuid.uuid4())
    
    query = """
    MATCH (t:ThemeBase {id: $tid})
    MATCH (u:User {id: $uid})
    
    // 1. Find Active ThemeVersion
    MATCH (t)-[:HAS_VERSION]->(tv:ThemeVersion)
    WHERE tv.status = 'active' AND tv.valid_to IS NULL
    
    WITH DISTINCT t, u, tv
    
    // 2. Create FactorBase
    CREATE (fb:FactorBase {
        id: $fid,
        created_at: datetime(),
        created_by: $uid
    })
    CREATE (u)-[:CREATED]->(fb)
    CREATE (t)-[:HAS_FACTOR]->(fb) // Base-to-Base link? Or just Project structure? 
    // Schema says Theme->Factor is getting deprecated/confusing with versions.
    // But helpful for global search via ThemeBase. Let's keep it for now as "Is Associated With".
    
    // 3. Create FactorVersion
    CREATE (fv:FactorVersion {
        id: $vid,
        base_id: $fid,
        name: $name,
        description: $desc,
        type: $type,
        version_id: tv.id,
        created_at: datetime(),
        valid_from: datetime(),
        valid_to: NULL
    })
    CREATE (fb)-[:HAS_VERSION]->(fv) // Base -> Version
    CREATE (tv)-[:HAS_FACTOR]->(fv)
    
    RETURN fb.id as id // Return Base ID to be consistent with "Entity Identity"
    """
    
    with driver.session() as session:
        result = session.run(query, {
                "fid": fid, 
                "vid": vid, 
                "name": name, 
                "desc": description, 
                "type": type, 
                "tid": theme_id,
                "uid": author_id
        })
        record = result.single()
        if not record:
            raise ValueError(f"Theme {theme_id} not found or has no active version.")
        return record["id"]

async def update_factor_manual(factor_id: str, name: Optional[str], description: Optional[str], type: Optional[str], theme_id: Optional[str]):
    driver = get_driver()
    
    if not theme_id:
        # Fallback/Legacy Attempt: Update by ID directly if it's a legacy Factor node
        query = """
        MATCH (f:FactorBase {id: $id})
        SET f.name = coalesce($name, f.name), 
            f.description = coalesce($desc, f.description),
            f.type = coalesce($type, f.type)
        """
        with driver.session() as session:
            session.run(query, {"id": factor_id, "name": name, "desc": description, "type": type})
        return

    # Versioned Update
    query = """
    MATCH (t:ThemeBase {id: $tid})
    MATCH (t)-[:HAS_VERSION]->(tv:ThemeVersion)
    WHERE tv.status = 'active' AND tv.valid_to IS NULL
    
    MATCH (fb:FactorBase {id: $fid})
    MATCH (tv)-[:HAS_FACTOR]->(fv:FactorVersion)
    WHERE fv.base_id = fb.id
    
    SET fv.name = coalesce($name, fv.name), 
        fv.description = coalesce($desc, fv.description),
        fv.type = coalesce($type, fv.type)
    """
    with driver.session() as session:
        session.run(query, {"fid": factor_id, "tid": theme_id, "name": name, "desc": description, "type": type})

async def delete_factor_manual(factor_id: str):
    driver = get_driver()
    # Delete the FactorVersion from the ACTIVE ThemeVersion(s) associated with this Base ID.
    query = """
    MATCH (fb:FactorBase {id: $id})
    MATCH (fb)-[:HAS_VERSION]->(fv:FactorVersion)
    MATCH (tv:ThemeVersion)-[:HAS_FACTOR]->(fv)
    WHERE tv.status = 'active' AND tv.valid_to IS NULL
    DETACH DELETE fv
    """
    with driver.session() as session:
        session.run(query, {"id": factor_id})

async def create_claim_manual(theme_id: str, source_id: str, target_id: str, statement: str, author_id: str, polarity: str = "+", confidence: float = 1.0) -> str:
    """
    Creates ClaimBase + ClaimVersion.
    Resolves Source/Target Base IDs to their Active Versions in the current Theme Version.
    """
    driver = get_driver()
    cid = str(uuid.uuid4())
    vid = str(uuid.uuid4())
    
    query = """
    MATCH (theme:ThemeBase {id: $thid})
    MATCH (u:User {id: $uid})
    
    // 1. Find Active ThemeVersion
    MATCH (theme)-[:HAS_VERSION]->(tv:ThemeVersion)
    WHERE tv.status = 'active' AND tv.valid_to IS NULL
    
    // 2. Resolve Source/Target Factors (Base -> Active Version)
    // We look for FactorVersions BELONGING TO this active ThemeVersion that link to the given Base IDs
    MATCH (tv)-[:HAS_FACTOR]->(fv_source:FactorVersion {base_id: $sid})
    MATCH (tv)-[:HAS_FACTOR]->(fv_target:FactorVersion {base_id: $tid})
    
    WITH DISTINCT theme, u, tv, fv_source, fv_target
    
    // 3. Create ClaimBase
    CREATE (cb:ClaimBase {
        id: $cid,
        created_at: datetime(),
        created_by: $uid
    })
    CREATE (u)-[:CREATED]->(cb)
    
    // 4. Create ClaimVersion
    CREATE (cv:ClaimVersion {
        id: $vid,
        base_id: $cid,
        statement: $stmt,
        polarity: $pol,
        confidence: $conf,
        source_version_id: fv_source.id,
        target_version_id: fv_target.id,
        created_at: datetime(),
        valid_from: datetime(),
        valid_to: NULL
    })
    CREATE (cb)-[:HAS_VERSION]->(cv) // Base -> Version
    
    // 5. Link ClaimVersion to FactorVersions
    CREATE (fv_source)-[:CLAIMS]->(cv)
    CREATE (cv)-[:TO]->(fv_target)
    
    RETURN cb.id as id // Return Base ID
    """
    
    with driver.session() as session:
        result = session.run(query, {
            "cid": cid, 
            "vid": vid,
            "sid": source_id, 
            "tid": target_id, 
            "stmt": statement, 
            "pol": polarity, 
            "conf": confidence, 
            "thid": theme_id,
            "uid": author_id
        })
        record = result.single()
        if not record:
             raise ValueError("Could not create claim. Ensure Theme and Factors exist and are active in the current version.")
        return record["id"]

async def delete_claim_manual(claim_id: str):
    driver = get_driver()
    query = """
    MATCH (cb:ClaimBase {id: $id})
    MATCH (cb)-[:HAS_VERSION]->(cv:ClaimVersion)
    WHERE cv.valid_to IS NULL
    DETACH DELETE cv
    """
    with driver.session() as session:
        session.run(query, {"id": claim_id})

async def create_decision(theme_id: str, description: str, author_id: str) -> str:
    """
    Finalizes the current ThemeVersion and creates a new one by Deep Copying all data.
    Implements Base/Version Snapshot with Lineage:
    - Closes active ThemeVersion.
    - Creates active ThemeVersion.
    - Deep Copies FactorVersions (maintaining base_id).
    - Deep Copies ClaimVersions (maintaining base_id, reconnecting to new FactorVersions).
    - Adds [:DERIVED_FROM] relationships for all copied elements.
    """
    driver = get_driver()
    did = str(uuid.uuid4())
    new_version_id = str(uuid.uuid4())
    
    # 1. Create Decision & Version Transition
    # Returns the old version ID to facilitate copying
    q_create_ver = """
    MATCH (t:ThemeBase {id: $tid})
    MATCH (u:User {id: $uid})
    
    // Find Current Active Version
    MATCH (t)-[:HAS_VERSION]->(old_v:ThemeVersion)
    WHERE old_v.status = 'active' AND old_v.valid_to IS NULL
    WITH DISTINCT t, old_v, u
    
    // Create Decision
    CREATE (d:Decision {
        id: $did, 
        description: $desc, 
        timestamp: datetime()
    })
    CREATE (u)-[:CREATED]->(d)
    MERGE (old_v)-[:DECIDED_BY]->(d)
    
    // Close Old Version
    SET old_v.valid_to = datetime()
    SET old_v.status = 'historical'
    
    WITH old_v, t
    
    // Remove old active relationship
    MATCH (t)-[r_active:HAS_ACTIVE_VERSION]->(old_v)
    DELETE r_active
    
    // Create New Version
    CREATE (new_v:ThemeVersion {
        id: $new_vid,
        base_id: t.id,
        name: old_v.name, 
        description: old_v.description,
        status: 'active',
        created_at: datetime(),
        valid_from: datetime(),
        valid_to: NULL
    })
    CREATE (t)-[:HAS_VERSION]->(new_v)
    CREATE (t)-[:HAS_ACTIVE_VERSION]->(new_v)
    CREATE (d)-[:RESULTED_IN]->(new_v)
    CREATE (new_v)-[:DERIVED_FROM]->(old_v)
    
    // Copy Role (Fixes access control)
    // Copy all explicit roles from old version to new version
    WITH new_v, old_v
    MATCH (old_v)<-[r_role:HAS_ROLE]-(member:User)
    MERGE (member)-[:HAS_ROLE {role: r_role.role}]->(new_v)
    
    RETURN new_v.id as new_id, old_v.id as old_id
    """

    # 2. Copy Factors
    q_copy_factors = """
    MATCH (old_v:ThemeVersion {id: $old_id})
    MATCH (new_v:ThemeVersion {id: $new_id})
    MATCH (old_v)-[:HAS_FACTOR]->(old_f:FactorVersion)
    WITH DISTINCT old_v, new_v, old_f
    
    CREATE (new_f:FactorVersion {
        id: randomUUID(),
        base_id: old_f.base_id,
        name: old_f.name,
        type: old_f.type,
        description: old_f.description,
        version_id: new_v.id,
        created_at: datetime(),
        valid_from: datetime(),
        valid_to: NULL
    })
    CREATE (new_v)-[:HAS_FACTOR]->(new_f)
    CREATE (new_f)-[:DERIVED_FROM]->(old_f)
    SET old_f.valid_to = datetime()
    
    // Link to Base
    WITH new_f, old_f
    MATCH (fb:FactorBase {id: old_f.base_id})
    MERGE (fb)-[:HAS_VERSION]->(new_f)
    """

    # 3. Copy Claims
    q_copy_claims = """
    MATCH (new_v:ThemeVersion {id: $new_id})
    // Resolve old claims via lineage of factors
    // Find new factors in new version
    MATCH (new_v)-[:HAS_FACTOR]->(new_f_source:FactorVersion)
    MATCH (new_f_source)-[:DERIVED_FROM]->(old_f_source:FactorVersion)
    
    // Traverse to old claim
    MATCH (old_f_source)-[:CLAIMS]->(old_c:ClaimVersion)-[:TO]->(old_f_target:FactorVersion)
    
    // Resolve new target factor
    MATCH (new_f_target:FactorVersion)-[:DERIVED_FROM]->(old_f_target)
    WHERE (new_v)-[:HAS_FACTOR]->(new_f_target)
    
    // Create new claim
    CREATE (new_c:ClaimVersion {
        id: randomUUID(),
        base_id: old_c.base_id,
        statement: old_c.statement,
        confidence: old_c.confidence,
        polarity: old_c.polarity,
        source_version_id: new_f_source.id,
        target_version_id: new_f_target.id,
        created_at: datetime(),
        valid_from: datetime(),
        valid_to: NULL
    })
    
    CREATE (new_f_source)-[:CLAIMS]->(new_c)
    CREATE (new_c)-[:TO]->(new_f_target)
    CREATE (new_c)-[:DERIVED_FROM]->(old_c)
    CREATE (new_v)-[:HAS_CLAIM]->(new_c)
    SET old_c.valid_to = datetime()
    
    // Link to Base
    WITH new_c, old_c
    MATCH (cb:ClaimBase {id: old_c.base_id})
    MERGE (cb)-[:HAS_VERSION]->(new_c)
    """

    with driver.session() as session:
        # Step 1: Create Version
        result = session.run(q_create_ver, {
            "tid": theme_id, 
            "did": did, 
            "desc": description, 
            "uid": author_id,
            "new_vid": new_version_id
        }).single()
        
        if not result:
            raise ValueError(f"Failed to create decision. Check if theme {theme_id} exists and has an active version.")
            
        old_version_id = result["old_id"]
        
        # Step 2: Copy Factors (Empty if no factors)
        session.run(q_copy_factors, {"old_id": old_version_id, "new_id": new_version_id})
        
        # Step 3: Copy Claims (Empty if no claims)
        session.run(q_copy_claims, {"new_id": new_version_id})
        
        return new_version_id

async def update_claim_manual(claim_id: str, statement: Optional[str], polarity: Optional[str], confidence: Optional[float], source_id: Optional[str], target_id: Optional[str]):
    driver = get_driver()
    query = """
    MATCH (cb:ClaimBase {id: $id})
    MATCH (cb)-[:HAS_VERSION]->(cv:ClaimVersion)
    WHERE cv.valid_to IS NULL
    SET cv.statement = coalesce($stmt, cv.statement),
        cv.polarity = coalesce($pol, cv.polarity),
        cv.confidence = coalesce($conf, cv.confidence)
    """
    with driver.session() as session:
        session.run(query, {"id": claim_id, "stmt": statement, "pol": polarity, "conf": confidence})



# --- Conversation Threads (Restored) ---

async def create_conversation_thread(target_id: str, topic: str) -> str:
    driver = get_driver()
    tid = str(uuid.uuid4())
    # Generic link: any node 's' with id=target_id
    # CRITICAL FIX: Ensure we are targeting a Version node if possible, or support generic attachment.
    # The frontend is expected to pass the Version ID (ThemeVersion, FactorVersion, etc.)
    # If the user passes a Base ID, it might legally attach to the Base, but usually we want context.
    # We will trust the ID passed, but add logging if it looks like a Base ID attached.
    query = """
    MATCH (s {id: $sid})
    CREATE (t:ConversationThread {id: $id, topic: $topic, status: 'active', created_at: datetime(), target_id: $sid})
    CREATE (s)-[:HAS_THREAD]->(t)
    RETURN t.id as id
    """
    with driver.session() as session:
        return session.run(query, {"sid": target_id, "id": tid, "topic": topic}).single()["id"]

async def get_threads_by_target(target_id: str) -> List[Dict]:
    driver = get_driver()
    query = """
    MATCH (s)
    WHERE s.id = $sid
    MATCH (s)-[:HAS_THREAD]->(t:ConversationThread)
    OPTIONAL MATCH (t)<-[:BELONGS_TO]-(m:ConversationMessage)
    WITH t, s, count(m) as msg_count
    RETURN {
        id: t.id,
        topic: t.topic,
        status: t.status,
        created_at: toString(t.created_at),
        target_id: s.id,
        message_count: msg_count
    } as thread_data
    """
    with driver.session() as session:
        return [r["thread_data"] for r in session.run(query, {"sid": target_id})]

async def get_thread_counts(target_ids: List[str]) -> Dict[str, int]:
    if not target_ids:
        return {}
    driver = get_driver()
    query = """
    MATCH (s)
    WHERE s.id IN $target_ids
    MATCH (s)-[:HAS_THREAD]->(t:ConversationThread)
    RETURN s.id as target_id, count(t) as thread_count
    """
    with driver.session() as session:
        result = session.run(query, {"target_ids": target_ids})
        return {r["target_id"]: r["thread_count"] for r in result}

async def create_thread_message(thread_id: str, user_id: str, content: str) -> Dict[str, Any]:
    driver = get_driver()
    msg_id = str(uuid.uuid4())
    query = """
    MATCH (t:ConversationThread {id: $tid})
    MATCH (u:User {id: $uid})
    CREATE (m:ConversationMessage {id: $mid, content: $content, created_at: datetime(), user_id: $uid})
    CREATE (m)-[:BELONGS_TO]->(t)
    CREATE (u)-[:AUTHORED]->(m)
    RETURN {
        id: m.id,
        content: m.content,
        created_at: toString(m.created_at),
        user_id: m.user_id,
        author_name: coalesce(u.name, u.email)
    } as msg
    """
    with driver.session() as session:
        return session.run(query, {"tid": thread_id, "mid": msg_id, "content": content, "uid": user_id}).single()["msg"]

async def get_thread_messages(thread_id: str) -> List[Dict[str, Any]]:
    driver = get_driver()
    query = """
    MATCH (m:ConversationMessage)-[:BELONGS_TO]->(t:ConversationThread {id: $tid})
    OPTIONAL MATCH (u:User)-[:AUTHORED]->(m)
    RETURN {
        id: m.id,
        content: m.content,
        created_at: toString(m.created_at),
        user_id: m.user_id,
        author_name: coalesce(u.name, u.email, 'Unknown')
    } as msg
    ORDER BY m.created_at ASC
    """
    with driver.session() as session:
        return [r["msg"] for r in session.run(query, {"tid": thread_id})]
