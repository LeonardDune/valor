import logging
from typing import List, Dict, Optional
from app.db.utils import get_driver
from app.models.domain import Role, LifecycleStatus

logger = logging.getLogger(__name__)

async def get_user_environments(user_id: str) -> List[Dict]:
    """
    Recursively fetches the environment hierarchy for a user.
    Organization -> Projects -> Themes
    Includes status and proposal counts.
    """
    driver = get_driver()
    
    # This query finds all organizations the user is a member of,
    # then finds all projects in those orgs that the user is a member of,
    # then finds all themes in those projects that the user is a member of.
    # It constructs a nested JSON structure.
    # Note: We filter by explicit membership or ADMIN role implication if required,
    # but for now we stick to explicit MEMBER_OF relationships or ADMIN roles on parents.
    
    query = """
    MATCH (u:User {id: $uid})
    
    // 1. Find Organizations via multiple paths
    // Path A: Direct Organization Membership
    OPTIONAL MATCH (u)-[r_direct:HAS_ROLE]->(org_direct:Organization)
    
    // Path B: Project Membership -> owning Org
    OPTIONAL MATCH (u)-[r_proj_indirect:HAS_ROLE]->(:Project)<-[:OWNS]-(org_proj:Organization)
    
    // Path C: Theme Membership -> owning Project -> owning Org
    OPTIONAL MATCH (u)-[r_theme_indirect:HAS_ROLE]->(:Theme)<-[:HAS_THEME]-(:Project)<-[:OWNS]-(org_theme:Organization)
    
    // Combine all reachable Orgs
    WITH u, 
         collect({node: org_direct, role: r_direct.role}) + 
         collect({node: org_proj, role: null}) + 
         collect({node: org_theme, role: null}) as org_list
         
    UNWIND org_list as item
    WITH item.node as org, item.role as raw_role, u
    WHERE org IS NOT NULL
    
    // Deduplicate: Group by Org and pick highest role (no implicit admin anymore)
    WITH org, u, collect(raw_role) as roles
    WITH org, u, 
         CASE WHEN 'admin' IN roles THEN 'admin' ELSE head(roles) END as user_role

    // FILTER: Hide archived orgs UNLESS user is admin
    WITH org, user_role, u
    WHERE (org.status IS NULL OR org.status <> 'archived') OR (user_role = 'admin')
    
    // 2. Find Projects in those Orgs
    OPTIONAL MATCH (org)-[:OWNS]->(proj:Project)
    // Check direct project role OR org admin role OR platform admin
    OPTIONAL MATCH (u)-[r_proj:HAS_ROLE]->(proj)
    
    WITH u, org, user_role, proj, r_proj
    // Determine Project Role
    WITH u, org, user_role, proj,
         CASE 
            WHEN u.is_platform_admin = true OR user_role = 'admin' THEN 'admin'
            ELSE coalesce(r_proj.role, 'member') 
         END as proj_role
         
    // FILTER: Hide archived projects UNLESS user is admin (or project admin)
    WHERE proj IS NULL OR ((proj.status IS NULL OR proj.status <> 'archived') OR (proj_role = 'admin'))
    
    // 3. Find Themes in those Projects
    OPTIONAL MATCH (proj)-[:HAS_THEME]->(theme:Theme)
    // Check direct theme role OR project/org admin role OR platform admin
    OPTIONAL MATCH (u)-[r_theme:HAS_ROLE]->(theme)
    
    WITH u, org, user_role, proj, proj_role, theme, r_theme
    
    // Determine Theme Role
    WITH u, org, user_role, proj, proj_role, theme,
         CASE
            WHEN u.is_platform_admin = true OR user_role = 'admin' OR proj_role = 'admin' THEN 'admin'
            ELSE coalesce(r_theme.role, 'member')
         END as theme_role
         
    // FILTER: Hide archived themes UNLESS user is admin
    WHERE theme IS NULL OR ((theme.status IS NULL OR theme.status <> 'archived') OR (theme_role = 'admin'))
    
    // Recalculate effective roles (redundant safety)
    // ...
    
    ORDER BY org.name, proj.name, theme.name
    
    // Aggregate Themes into Projects
    WITH org, user_role, proj, proj_role, collect(DISTINCT CASE WHEN theme IS NOT NULL THEN {
        id: theme.id,
        // FETCH FROM ACTIVE VERSION
        // We know 'av' is available if we matched it, but we need to match it first.
        // Wait, I need to match it upstream or inside the WITH.
        // It's cleaner to do an OPTIONAL MATCH before the aggregation.
        // Let's modify the query structure slightly.
        name: head([ (theme)-[:HAS_ACTIVE_VERSION]->(v) | v.name ]), 
        description: head([ (theme)-[:HAS_ACTIVE_VERSION]->(v) | v.description ]),
        role: theme_role,
        status: theme.status,
        type: "THEME"
    } ELSE NULL END) as themes
    
    // Aggregate Projects into Orgs
    WITH org, user_role, collect(DISTINCT CASE WHEN proj IS NOT NULL THEN {
        id: proj.id,
        name: proj.name,
        description: proj.description,
        role: proj_role,
        status: proj.status,
        type: "PROJECT",
        themes: [x IN themes WHERE x IS NOT NULL]
    } ELSE NULL END) as projects
    
    RETURN collect({
        id: org.id,
        name: org.name,
        description: org.description,
        role: user_role,
        status: org.status,
        type: "ORGANIZATION",
        projects: [x IN projects WHERE x IS NOT NULL]
    }) as environments
    """
    
    try:
        with driver.session() as session:
            result = session.run(query, {"uid": user_id})
            record = result.single()
            if record and record["environments"]:
                return record["environments"]
            return []
    except Exception as e:
        logger.error(f"Failed to fetch user environments: {e}")
        return []

async def get_user_themes(user_id: str) -> List[Dict]:
    """
    Returns a flat list of themes the user has access to.
    Access can be via:
    1. Direct Theme Role
    2. Project Role (Admin cascades to all themes, Member usually sees themes)
    3. Organization Role (Admin cascades)
    4. Platform Admin (Sees all)
    """
    driver = get_driver()
    
    query = """
    MATCH (u:User {id: $uid})
    
    // 1. Find all accessible Themes via recursive permissions
    // This looks for any path from User -> ... -> Theme where a role exists
    // We simplify by looking for direct connections or upstream connections
    
    // Direct Theme Access
    OPTIONAL MATCH (u)-[r1:HAS_ROLE]->(t1:Theme)
    
    // Project Access (Cascading down)
    OPTIONAL MATCH (u)-[r2:HAS_ROLE]->(p:Project)-[:HAS_THEME]->(t2:Theme)
    
    // Organization Access (Cascading down)
    OPTIONAL MATCH (u)-[r3:HAS_ROLE]->(o:Organization)-[:OWNS]->(p2:Project)-[:HAS_THEME]->(t3:Theme)
    
    // Platform Admin (All Themes)
    OPTIONAL MATCH (t4:Theme)
    WHERE u.is_platform_admin = true
    
    // Collect all valid themes with their highest role found
    WITH u, 
         collect({t: t1, r: r1.role}) + 
         collect({t: t2, r: r2.role}) + 
         collect({t: t3, r: r3.role}) + 
         collect({t: t4, r: 'admin'}) as candidate_maps
    UNWIND candidate_maps as item
    WITH item.t as theme, u, item.r as role
    WHERE theme IS NOT NULL
    
    // Determine highest role per theme
    WITH theme, u,
         CASE 
            WHEN collect(role) CONTAINS 'admin' OR u.is_platform_admin = true THEN 'admin'
            ELSE 'member'
         END as effective_role
    
    // Now fetch context (Project + Organization) for each theme
    MATCH (org:Organization)-[:OWNS]->(proj:Project)-[:HAS_THEME]->(theme)
    
    // Check Archive Status Hierarchy
    WITH theme, effective_role, org, proj
    WHERE 
        // Show if ADMIN
        (effective_role = 'admin') OR 
        // OR if NOTHING in the chain is archived
        (
            (org.status IS NULL OR org.status <> 'archived') AND
            (proj.status IS NULL OR proj.status <> 'archived') AND
            (theme.status IS NULL OR theme.status <> 'archived')
        )
    
    // Optional: Get stats (claims, members)
    // Counting active claims
    OPTIONAL MATCH (theme)-[:HAS_FACTOR]->(f:Factor)
    WITH theme, effective_role, org, proj, count(f) as claim_count
    
    // Counting members
    OPTIONAL MATCH (member:User)-[:HAS_ROLE]->(theme)
    WITH theme, effective_role, org, proj, claim_count, count(member) as member_count

    RETURN {
        id: theme.id,
        name: head([ (theme)-[:HAS_ACTIVE_VERSION]->(v) | v.name ]),
        description: head([ (theme)-[:HAS_ACTIVE_VERSION]->(v) | v.description ]),
        project_name: proj.name,
        organization_name: org.name,
        role: effective_role,
        status: theme.status,
        is_archived: (theme.status = 'archived' OR proj.status = 'archived' OR org.status = 'archived'),
        stats: {
            active_claims: claim_count,
            members: member_count
        }
    } as theme_data
    ORDER BY theme.name
    """
    
    try:
        with driver.session() as session:
            result = session.run(query, {"uid": user_id})
            themes = [record["theme_data"] for record in result]
            return themes
    except Exception as e:
        logger.error(f"Failed to fetch user themes: {e}")
        return []
