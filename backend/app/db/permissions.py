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
                logger.info(f"Assigned role {role.value} to user {user_email} on entity {entity_id}")
            else:
                 logger.warning(f"Role assignment check: User {user_email} or Entity {entity_id} might not exist.")
    except Exception as e:
        logger.error(f"Failed to assign role: {e}")
        raise e

async def check_permission(user_id: str, entity_id: str, required_role: Role) -> bool:
    """
    Checks if a user has the required role (or better) on the entity OR any of its parents.
    Hierarchy: Theme -> Project -> Organization
    Roles: ADMIN > MEMBER > VIEWER
    """
    driver = get_driver()
    
    # We need to traverse UP from the entity to find if the user has a role on it or any parent.
    # We also need to check role hierarchy (Admin allows everything).
    
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
    // We look for any node 'parent' that recursively owns/contains 'target', 
    // AND where 'u' has a role on 'parent'.
    OPTIONAL MATCH (u)-[r:HAS_ROLE]->(parent)-[:OWNS|HAS_THEME|HAS_VERSION*0..]->(target)
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
            
            # Check if ANY of the found roles satisfy the requirement
            for role_str in user_roles:
                if role_str: # role can be None if OPTIONAL MATCH fails
                    weight = role_weights.get(role_str, 0)
                    if weight >= required_weight:
                        return True
            
            return False
            
    except Exception as e:
        logger.error(f"Failed to check permissions: {e}")
        return False

async def get_user_navigation_tree(user_id: str):
    """
    Returns a tree of entities the user has access to.
    
    Logic:
    1. Find all nodes where user has explicit role.
    2. Expand DOWN from those nodes if role is ADMIN? 
       Wait, requirements say: "Beheerder van project heeft ook rechten op thema's".
       So if User is Admin on Project P, they should see P and all its Themes.
       If User is Member on Theme T (but not Project), they should probably see Project P (as container) -> Theme T.
    
    Let's fetch all accessible nodes first.
    """
    driver = get_driver()
    
    # 1. Fetch all 'Root Access' nodes (where user has explicit role)
    # 2. If Admin, collect all descendants.
    # 3. If Member/Viewer, just that node? Or descendants too? 
    #    "Standrd regels": Admin cascades. Member usually implies access to that specific scope. 
    #    Assumption: Member on Project -> See Project + Themes? Or just Project?
    #    User request: "Administrator has cascading rights... Member in role of admin of a theme has no rights for project."
    #    It implies cascading is an ADMIN feature mostly. But usually Member of Project sees Themes too.
    #    Let's assume: access to a node implies read access to children for navigation, or at least we should list them.
    #    Actually, keeping it simple: Fetch all nodes U has access to via cascading rules.
    
    query = """
    MATCH (u:User {id: $uid})
    MATCH (u)-[r:HAS_ROLE]->(root_access_node)
    
    // 1. Collect descendants if Admin
    OPTIONAL MATCH (root_access_node)-[:OWNS|HAS_THEME*1..]->(child)
    WHERE r.role = 'admin'
    
    // 2. Identify all accessible nodes: the root ones + children if admin
    WITH u, collect(root_access_node) + collect(child) as accessible_nodes
    UNWIND accessible_nodes as node
    WITH u, node
    WHERE node IS NOT NULL
    
    // 3. For each accessible node, find its full path from Organization down to build the tree context
    MATCH path = (o:Organization)-[:OWNS|HAS_THEME*0..]->(node)
    
    // Return all distinct paths
    RETURN distinct [n in nodes(path) | {id: n.id, name: n.name, labels: labels(n), status: n.status}] as path_data
    """
    
    try:
        with driver.session() as session:
            result = session.run(query, {"uid": user_id})
            paths = [record["path_data"] for record in result]
            return _build_tree_from_paths(paths)
    except Exception as e:
        logger.error(f"Failed to get navigation tree: {e}")
        return []

def _build_tree_from_paths(paths):
    """
    Helper to merge list of paths into a nested tree structure.
    paths is list of lists of dicts: [[Org, Proj, Theme], [Org, Proj2], ...]
    """
    tree = []
    
    # Map to track current level nodes by ID
    # This is a simple recursive builder or iterative merge
    
    # Let's use a dictionary map for O(1) lookup
    # key: id, value: node_dict (with 'children' list)
    nodes_map = {}
    
    for path in paths:
        parent = None
        for item in path:
            nid = item['id']
            if nid not in nodes_map:
                # Create node
                new_node = item.copy()
                # Clean labels (neo4j returns list)
                lbls = new_node.get('labels', [])
                if 'Organization' in lbls: new_node['type'] = 'organization'
                elif 'Project' in lbls: new_node['type'] = 'project'
                elif 'Theme' in lbls: new_node['type'] = 'theme'
                else: new_node['type'] = 'unknown'
                del new_node['labels']
                
                new_node['children'] = []
                nodes_map[nid] = new_node
                
                # Add to tree roots if it's an Org (first item usually)
                if new_node['type'] == 'organization':
                     # Check if already in tree to avoid dupes at top level
                     if not any(n['id'] == nid for n in tree):
                         tree.append(new_node)
                
                # If we have a parent from this path, link it
                if parent:
                     # Check connection
                     if not any(child['id'] == nid for child in parent['children']):
                         parent['children'].append(new_node)
            
            # Move guidance pntr
            parent = nodes_map[nid]
            
    return tree
