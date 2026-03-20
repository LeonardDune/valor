# Re-export facade voor backwards-compatibiliteit.
# Alle logica zit in de domein-modules; importeer altijd vanuit crud.py.

from app.db.conversations import (
    save_claims,
    set_conversation_topic,
    get_conversation_topic,
    fetch_existing_factors,
    revoke_claims,
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
    get_theme_users,
    update_theme_member_role,
    remove_theme_member,
    get_theme_version_users,
    add_user_to_theme_version,
    update_theme_version_member_role,
    delete_theme_version_member,
)

from app.db.themes import (
    get_projects,
    create_project,
    update_project,
    archive_project,
    get_project_themes,
    create_theme,
    update_theme,
    archive_theme,
    create_theme_version,
    update_theme_version,
    archive_theme_version,
    get_theme_by_id_simple,
    get_theme_versions_by_theme,
    get_theme_version,
    get_theme_active_version,
    get_active_version_id_if_theme,
    get_project_id_by_theme,
    create_decision,
)


from app.db.permissions import check_permission
from app.db.utils import get_driver

__all__ = [
    # conversations
    "save_claims", "set_conversation_topic", "get_conversation_topic",
    "fetch_existing_factors", "revoke_claims",
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
    "get_theme_users", "update_theme_member_role", "remove_theme_member",
    "get_theme_version_users", "add_user_to_theme_version",
    "update_theme_version_member_role", "delete_theme_version_member",
    # themes
    "get_projects", "create_project", "update_project", "archive_project",
    "get_project_themes", "create_theme", "update_theme", "archive_theme",
    "create_theme_version", "update_theme_version", "archive_theme_version",
    "get_theme_by_id_simple", "get_theme_versions_by_theme", "get_theme_version",
    "get_theme_active_version", "get_active_version_id_if_theme",
    "get_project_id_by_theme", "create_decision",
    # shared
    "check_permission", "get_driver",
]
