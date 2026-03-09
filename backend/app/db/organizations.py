from typing import List, Optional, Dict
import uuid
import logging

from app.db.utils import get_driver

logger = logging.getLogger(__name__)


# --- Organization Core ---

async def create_organization(name: str, description: Optional[str] = None, owner_id: Optional[str] = None) -> str:
    driver = get_driver()
    org_id = str(uuid.uuid4())

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


# --- User Core ---

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


# Project/Theme member shortcuts (generic delegation)

async def get_project_users(project_id: str) -> List[Dict]:
    driver = get_driver()
    query = "MATCH (p:Project {id: $pid})<-[r:HAS_ROLE]-(u:User) RETURN u, r.role as role"
    with driver.session() as session:
        return [{"id": rec["u"]["id"], "name": rec["u"].get("name", ""), "email": rec["u"]["email"], "role": rec["role"]} for rec in session.run(query, {"pid": project_id})]


async def update_project_member_role(project_id: str, user_id: str, role: str, name: Optional[str] = None):
    await update_org_member_role(project_id, user_id, role, name)


async def remove_project_member(project_id: str, user_id: str):
    await remove_user_from_organization(project_id, user_id)


async def get_theme_users(theme_id: str) -> List[Dict]:
    driver = get_driver()
    query = "MATCH (t:ThemeBase {id: $tid})<-[r:HAS_ROLE]-(u:User) RETURN u, r.role as role"
    with driver.session() as session:
        return [{"id": rec["u"]["id"], "name": rec["u"].get("name", ""), "email": rec["u"]["email"], "role": rec["role"]} for rec in session.run(query, {"tid": theme_id})]


async def update_theme_member_role(theme_id: str, user_id: str, role: str, name: Optional[str] = None):
    await update_org_member_role(theme_id, user_id, role, name)


async def remove_theme_member(theme_id: str, user_id: str):
    await remove_user_from_organization(theme_id, user_id)


async def get_theme_version_users(version_id: str) -> List[Dict]:
    driver = get_driver()
    query = "MATCH (s:ThemeVersion {id: $sid})<-[r:HAS_ROLE]-(u:User) RETURN u, r.role as role"
    with driver.session() as session:
        return [{"id": rec["u"]["id"], "name": rec["u"].get("name", ""), "email": rec["u"]["email"], "role": rec["role"]} for rec in session.run(query, {"sid": version_id})]


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
