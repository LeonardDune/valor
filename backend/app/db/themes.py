from typing import List, Optional, Dict, Any
import uuid
import logging

from app.db.utils import get_driver

logger = logging.getLogger(__name__)


# --- Projects ---

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


# --- Themes ---

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
    query = """
    MATCH (t:ThemeBase {id: $id})
    SET t.status = 'archived'
    WITH t
    OPTIONAL MATCH (t)-[:HAS_VERSION]->(s:ThemeVersion)
    SET s.status = 'archived'
    """
    with driver.session() as session:
        session.run(query, {"id": theme_id})


# --- Theme Versions ---

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


async def get_active_version_id_if_theme(entity_id: str) -> str:
    """
    Checks if the entity_id belongs to a ThemeBase.
    If so, returns the ID of the currently ACTIVE ThemeVersion.
    If not, returns the entity_id as-is.
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
                logger.warning(f"Invite target is Theme {entity_id} but no active version found. Invite may fail strict checks.")
                return entity_id
        return entity_id


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


# --- Decisions / Version Transitions ---

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

    q_copy_factors = """
    MATCH (old_v:ThemeVersion {id: $old_id})
    MATCH (new_v:ThemeVersion {id: $new_id})
    MATCH (old_v)-[r:HAS_FACTOR]->(old_f:FactorVersion)
    WITH DISTINCT old_v, new_v, old_f, r

    CREATE (new_f:FactorVersion {
        id: randomUUID(),
        base_id: old_f.base_id,
        name: old_f.name,
        // type removed from node
        description: old_f.description,
        version_id: new_v.id,
        created_at: datetime(),
        valid_from: datetime(),
        valid_to: NULL
    })
    CREATE (new_v)-[:HAS_FACTOR {role: r.role}]->(new_f)
    CREATE (new_f)-[:DERIVED_FROM]->(old_f)
    SET old_f.valid_to = datetime()

    // Link to Base
    WITH new_f, old_f
    MATCH (fb:FactorBase {id: old_f.base_id})
    MERGE (fb)-[:HAS_VERSION]->(new_f)
    """

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
        evidence_text: old_c.evidence_text,
        evidence_url: old_c.evidence_url,
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

        session.run(q_copy_factors, {"old_id": old_version_id, "new_id": new_version_id})
        session.run(q_copy_claims, {"new_id": new_version_id})

        return new_version_id
