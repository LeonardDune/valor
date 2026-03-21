import logging
from typing import Optional, List
from neo4j import Transaction
from app.db.utils import get_driver
from app.models.domain import Role

logger = logging.getLogger(__name__)

async def assign_role(user_id: str, entity_id: str, role: Role):
    """
    Assigns a specific role to a user for a given entity (Org, Project, Theme).
    This creates or updates the HAS_ROLE relationship.
    """
    driver = get_driver()
    query = """
    MATCH (u:User {id: $uid})
    MATCH (e) WHERE e.id = $entity_id
    MERGE (u)-[r:HAS_ROLE]->(e)
    SET r.role = $role, r.updated_at = datetime(), r.status = coalesce(r.status, 'active')
    """
    try:
        with driver.session() as session:
            # ensure user exists? assuming user exists for now or call create_user in crud
            result = session.run(query, {"uid": user_id, "entity_id": entity_id, "role": role.value})
            info = result.consume()
            if info.counters.relationships_created > 0 or info.counters.properties_set > 0:
                logger.info(f"Assigned role {role.value} to user {user_id} on entity {entity_id}")
            else:
                logger.warning(f"Role assignment check: User {user_id} or Entity {entity_id} might not exist.")
    except Exception as e:
        logger.error(f"Failed to assign role: {e}")
        raise e

async def check_permission(user_id: str, entity_id: str, required_role: Role) -> bool:
    """
    Checks if a user has the required role (or better) on the entity OR any of its parents.
    Hierarchy: Organization -> Project -> Issue -> DesignSpace
    Roles: ADMIN > MODERATOR > MEMBER > VIEWER
    """
    driver = get_driver()

    from app.services.ontology_cache import get_rbac_role_weights
    role_weights = get_rbac_role_weights()
    if not role_weights:
        # Fallback tijdens startup vóór ontologie geladen is
        role_weights = {Role.ADMIN.value: 30, Role.MODERATOR.value: 25,
                        Role.MEMBER.value: 20, Role.VIEWER.value: 10}
    required_weight = role_weights.get(required_role.value, 0)

    query = """
    MATCH (target {id: $entity_id})
    MATCH (u:User {id: $uid})

    // Check Platform Admin
    WITH u, target, COALESCE(u.is_platform_admin, false) as is_platform_admin

    // Find highest role on any ancestor (including self)
    OPTIONAL MATCH (u)-[r:HAS_ROLE]->(parent)-[:OWNS|hasIssue|isAddressedInDesignSpace*0..]->(target)
    WHERE r.status IS NULL OR r.status = 'active'

    RETURN is_platform_admin, collect(r.role) as roles
    """

    try:
        with driver.session() as session:
            result = session.run(query, {"uid": user_id, "entity_id": entity_id})
            record = result.single()

            if not record:
                return False

            if record["is_platform_admin"]:
                return True

            user_roles = record["roles"]

            for role_str in user_roles:
                if role_str:
                    weight = role_weights.get(role_str, 0)
                    if weight >= required_weight:
                        return True

            return False

    except Exception as e:
        logger.error(f"Failed to check permissions: {e}")
        return False
