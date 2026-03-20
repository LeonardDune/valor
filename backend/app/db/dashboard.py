import logging
from typing import List, Dict
from app.db.utils import get_driver

logger = logging.getLogger(__name__)


async def get_user_environments(user_id: str) -> List[Dict]:
    """Haalt de omgevingshiërarchie op voor een gebruiker: Organization -> Projects -> Issues."""
    driver = get_driver()

    query = """
    MATCH (u:User {id: $uid})

    // 1. Vind Organizaties via meerdere paden
    OPTIONAL MATCH (u)-[r_direct:HAS_ROLE]->(org_direct:Organization)
    OPTIONAL MATCH (u)-[r_proj_indirect:HAS_ROLE]->(:Project)<-[:OWNS]-(org_proj:Organization)
    OPTIONAL MATCH (u)-[r_ds_indirect:HAS_ROLE]->(:DesignSpace)<-[:isAddressedInDesignSpace]-(:Issue)<-[:hasIssue]-(:Project)<-[:OWNS]-(org_ds:Organization)

    WITH u,
         collect({node: org_direct, role: r_direct.role}) +
         collect({node: org_proj, role: null}) +
         collect({node: org_ds, role: null}) AS org_list

    UNWIND org_list AS item
    WITH item.node AS org, item.role AS raw_role, u
    WHERE org IS NOT NULL

    WITH org, u, collect(raw_role) AS roles
    WITH org, u,
         CASE WHEN 'admin' IN roles THEN 'admin' ELSE head(roles) END AS user_role

    WITH org, user_role, u
    WHERE (org.status IS NULL OR org.status <> 'archived') OR (user_role = 'admin')

    // 2. Vind Projects
    OPTIONAL MATCH (org)-[:OWNS]->(proj:Project)
    OPTIONAL MATCH (u)-[r_proj:HAS_ROLE]->(proj)

    WITH u, org, user_role, proj, r_proj
    WITH u, org, user_role, proj,
         CASE
           WHEN u.is_platform_admin = true OR user_role = 'admin' THEN 'admin'
           ELSE coalesce(r_proj.role, 'member')
         END AS proj_role

    WHERE proj IS NULL OR ((proj.status IS NULL OR proj.status <> 'archived') OR (proj_role = 'admin'))

    // 3. Vind Issues via DesignSpace
    OPTIONAL MATCH (proj)-[:hasIssue]->(issue:Issue)-[:isAddressedInDesignSpace]->(ds:DesignSpace)
    OPTIONAL MATCH (u)-[r_ds:HAS_ROLE]->(ds)

    WITH u, org, user_role, proj, proj_role, issue, ds, r_ds
    WITH u, org, user_role, proj, proj_role, issue, ds,
         CASE
           WHEN u.is_platform_admin = true OR user_role = 'admin' OR proj_role = 'admin' THEN 'admin'
           ELSE coalesce(r_ds.role, 'member')
         END AS issue_role

    WHERE issue IS NULL OR ((issue.status IS NULL OR issue.status <> 'archived') OR (issue_role = 'admin'))

    ORDER BY org.name, proj.name, issue.name

    WITH org, user_role, proj, proj_role,
         collect(DISTINCT CASE WHEN issue IS NOT NULL THEN {
             id: issue.id,
             ds_id: ds.id,
             name: issue.name,
             description: issue.description,
             role: issue_role,
             status: issue.status,
             current_phase: ds.current_phase,
             type: "ISSUE"
         } ELSE NULL END) AS issues

    WITH org, user_role,
         collect(DISTINCT CASE WHEN proj IS NOT NULL THEN {
             id: proj.id,
             name: proj.name,
             description: proj.description,
             role: proj_role,
             status: proj.status,
             type: "PROJECT",
             issues: [x IN issues WHERE x IS NOT NULL]
         } ELSE NULL END) AS projects

    RETURN collect({
        id: org.id,
        name: org.name,
        description: org.description,
        role: user_role,
        status: org.status,
        type: "ORGANIZATION",
        projects: [x IN projects WHERE x IS NOT NULL]
    }) AS environments
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
    """Retourneert een platte lijst van Issues/DesignSpaces die de gebruiker kan bereiken."""
    driver = get_driver()

    query = """
    MATCH (u:User {id: $uid})

    OPTIONAL MATCH (u)-[r1:HAS_ROLE]->(ds1:DesignSpace)
    OPTIONAL MATCH (u)-[r2:HAS_ROLE]->(p:Project)-[:hasIssue]->(:Issue)-[:isAddressedInDesignSpace]->(ds2:DesignSpace)
    OPTIONAL MATCH (u)-[r3:HAS_ROLE]->(o:Organization)-[:OWNS]->(:Project)-[:hasIssue]->(:Issue)-[:isAddressedInDesignSpace]->(ds3:DesignSpace)
    OPTIONAL MATCH (ds4:DesignSpace)
    WHERE u.is_platform_admin = true

    WITH u,
         collect({ds: ds1, r: r1.role}) +
         collect({ds: ds2, r: r2.role}) +
         collect({ds: ds3, r: r3.role}) +
         collect({ds: ds4, r: 'admin'}) AS candidates
    UNWIND candidates AS item
    WITH item.ds AS ds, u, item.r AS role
    WHERE ds IS NOT NULL

    WITH ds, u,
         CASE
           WHEN collect(role) CONTAINS 'admin' OR u.is_platform_admin = true THEN 'admin'
           ELSE 'member'
         END AS effective_role

    MATCH (org:Organization)-[:OWNS]->(proj:Project)-[:hasIssue]->(issue:Issue)-[:isAddressedInDesignSpace]->(ds)

    WITH ds, effective_role, org, proj, issue
    WHERE
        (effective_role = 'admin') OR
        (
            (org.status IS NULL OR org.status <> 'archived') AND
            (proj.status IS NULL OR proj.status <> 'archived') AND
            (issue.status IS NULL OR issue.status <> 'archived')
        )

    RETURN {
        id: issue.id,
        ds_id: ds.id,
        name: issue.name,
        description: issue.description,
        project_name: proj.name,
        organization_name: org.name,
        role: effective_role,
        status: issue.status,
        current_phase: ds.current_phase,
        is_archived: (issue.status = 'archived' OR proj.status = 'archived' OR org.status = 'archived')
    } AS theme_data
    ORDER BY issue.name
    """

    try:
        with driver.session() as session:
            result = session.run(query, {"uid": user_id})
            return [record["theme_data"] for record in result]
    except Exception as e:
        logger.error(f"Failed to fetch user themes: {e}")
        return []
