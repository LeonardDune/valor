# Re-export facade voor backwards-compatibiliteit.
# Alle logica zit in de domein-modules; importeer altijd vanuit crud.py.

from app.db.conversations import (
    set_conversation_topic,
    get_conversation_topic,
    create_proposal,
    get_proposals,
    get_proposal_by_id,
    update_proposal_status,
    create_conversation_thread,
    get_threads_by_target,
    get_thread_counts,
    create_thread_message,
    get_thread_messages,
)

from app.db.organizations import (
    create_organization,
    get_organizations,
    get_user_organizations,
    update_organization,
    archive_organization,
    create_user,
    get_user_by_id,
    ensure_user_sync,
    get_user_by_email,
    get_all_users,
    update_user_profile,
    get_organization_users,
    add_user_to_organization,
    update_org_member_role,
    remove_user_from_organization,
    get_project_users,
    update_project_member_role,
    remove_project_member,
)

from app.db.issues import (
    create_issue_with_designspace,
    get_issue,
    update_issue,
    archive_issue,
    get_issues_by_project,
)

from app.db.designspace import (
    create_design_space,
    get_design_space_meta,
    set_design_space_phase,
    get_design_spaces_by_project,
    get_designspace_with_issue,
    get_designspace_members,
    add_designspace_member,
    update_designspace_member_role,
    remove_designspace_member,
    get_project_id_by_designspace,
)

# Project-functies zitten nu in organizations.py
from app.db.organizations import (
    create_user as _create_user,
)

# Project CRUD zat in themes.py — nu inlined hier via een kleine shim
import uuid
import logging
from typing import Optional, List, Dict
from app.db.utils import get_driver

logger = logging.getLogger(__name__)


async def get_projects(organization_id: str, user_id: str) -> List[Dict]:
    driver = get_driver()
    query = """
    MATCH (org:Organization {id: $oid})
    MATCH (u:User {id: $uid})
    OPTIONAL MATCH (u)-[r_org:HAS_ROLE]->(org)
    WITH org, u, coalesce(r_org.role, 'member') as org_role_direct
    WITH org, u,
         CASE WHEN u.is_platform_admin = true OR org_role_direct = 'admin' THEN 'admin' ELSE 'member' END as org_role
    MATCH (org)-[:OWNS]->(p:Project)
    WHERE p.status IS NULL OR p.status <> 'archived'
    OPTIONAL MATCH (u)-[r_proj:HAS_ROLE]->(p)
    WITH org, u, org_role, p,
         CASE
            WHEN org_role = 'admin' THEN 'admin'
            ELSE coalesce(r_proj.role, 'member')
         END as proj_role
    OPTIONAL MATCH (p)-[:hasIssue]->(i:Issue)
    WHERE i.status IS NULL OR i.status <> 'archived'
    WITH p, proj_role, org, collect(i) as issues
    RETURN {
        id: p.id,
        name: p.name,
        description: p.description,
        organization_name: org.name,
        organization_id: org.id,
        role: proj_role,
        status: p.status,
        type: 'PROJECT',
        issues: issues,
        created_at: toString(p.created_at)
    } as project_data
    """
    with driver.session() as session:
        return [r["project_data"] for r in session.run(query, {"oid": organization_id, "uid": user_id})]


async def create_project(name: str, organization_id: str, description: Optional[str] = None, owner_id: Optional[str] = None) -> str:
    driver = get_driver()
    pid = str(uuid.uuid4())
    query = "MATCH (o:Organization {id: $oid})"
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
    OPTIONAL MATCH (p)-[:hasIssue]->(i:Issue)
    SET i.status = 'archived'
    WITH i
    OPTIONAL MATCH (i)-[:isAddressedInDesignSpace]->(ds:DesignSpace)
    SET ds.status = 'archived'
    """
    with driver.session() as session:
        session.run(query, {"id": project_id})


from app.db.permissions import check_permission
from app.db.utils import get_driver

__all__ = [
    # conversations
    "set_conversation_topic", "get_conversation_topic",
    "create_proposal", "get_proposals", "get_proposal_by_id", "update_proposal_status",
    "create_conversation_thread", "get_threads_by_target", "get_thread_counts",
    "create_thread_message", "get_thread_messages",
    # organizations
    "create_organization", "get_organizations", "get_user_organizations",
    "update_organization", "archive_organization",
    "create_user", "get_user_by_id", "ensure_user_sync", "get_user_by_email",
    "get_all_users", "update_user_profile",
    "get_organization_users", "add_user_to_organization", "update_org_member_role",
    "remove_user_from_organization",
    "get_project_users", "update_project_member_role", "remove_project_member",
    # projects
    "get_projects", "create_project", "update_project", "archive_project",
    # issues
    "create_issue_with_designspace", "get_issue", "update_issue", "archive_issue",
    "get_issues_by_project",
    # designspace
    "create_design_space", "get_design_space_meta", "set_design_space_phase",
    "get_design_spaces_by_project", "get_designspace_with_issue",
    "get_designspace_members", "add_designspace_member", "update_designspace_member_role",
    "remove_designspace_member", "get_project_id_by_designspace",
    # shared
    "check_permission", "get_driver",
]
