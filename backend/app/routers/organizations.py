from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel
import logging

from app.auth import get_current_user
from app.models.domain import Role, InviteStatus
from app.db.crud import (
    create_organization, get_organizations, create_user,
    get_organization_users, add_user_to_organization, update_org_member_role,
    remove_user_from_organization, update_user_profile, get_user_organizations,
    get_user_by_email, check_permission, get_all_users,
    update_organization, archive_organization,
    update_project_member_role, remove_project_member,
    update_theme_member_role, remove_theme_member,
    get_user_by_id,
)
from app.db.invites import create_invite, get_pending_invites, accept_invite

logger = logging.getLogger(__name__)

router = APIRouter()


class OrganizationCreate(BaseModel):
    name: str
    description: Optional[str] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class UserCreate(BaseModel):
    email: str
    name: Optional[str] = None


class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None


class AddMemberRequest(BaseModel):
    email: str
    role: str = "member"


class UpdateMemberRequest(BaseModel):
    role: str
    name: Optional[str] = None
    status: Optional[str] = None


class InviteRequest(BaseModel):
    email: str
    entity_id: str
    role: str = "member"
    expires_in_days: Optional[int] = 7
    redirect_url: Optional[str] = None


class InviteAcceptRequest(BaseModel):
    code: str


# --- Organization routes ---

@router.get("/organizations")
async def list_organizations(user: dict = Depends(get_current_user)):
    email = user.get("email")
    if not email:
        return []

    current_user_data = await get_user_by_email(email)
    is_admin = current_user_data and current_user_data.get('is_platform_admin')

    if is_admin:
        logger.info(f"Platform Admin {email} requesting all organizations")
        orgs = await get_organizations()
    else:
        logger.info(f"Checking organizations for user: {email}")
        orgs = await get_user_organizations(user["id"])

    logger.info(f"Found {len(orgs)} organizations for user {email} (Admin: {is_admin})")
    return orgs


@router.post("/organizations")
async def create_new_organization(org: OrganizationCreate, user: dict = Depends(get_current_user)):
    oid = await create_organization(org.name, org.description, owner_id=user["id"])
    return {"id": oid, "name": org.name}


@router.patch("/organizations/{org_id}")
async def update_org(org_id: str, data: OrganizationUpdate, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], org_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to edit this organization")
    await update_organization(org_id, data.name, data.description)
    return {"status": "updated"}


@router.delete("/organizations/{org_id}")
async def archive_org_endpoint(org_id: str, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], org_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to archive this organization")
    await archive_organization(org_id)
    return {"status": "archived"}


# --- User routes ---

@router.post("/users")
async def create_new_user(user: UserCreate, user_auth: dict = Depends(get_current_user)):
    uid = await create_user(user.email, user.name)
    return {"id": uid, "email": user.email}


@router.put("/users/me")
async def update_my_profile(profile: UserProfileUpdate, user: dict = Depends(get_current_user)):
    email = user.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="User email not found in token")
    await update_user_profile(email, profile.first_name, profile.last_name, profile.username)
    return {"status": "updated", "email": email}


@router.get("/users/me")
async def get_current_user_profile(user: dict = Depends(get_current_user)):
    return user


@router.get("/users")
async def list_all_users(user: dict = Depends(get_current_user)):
    current_user_data = await get_user_by_id(user["id"])
    if not current_user_data or not current_user_data.get('is_platform_admin'):
        raise HTTPException(status_code=403, detail="Only Platform Admins can view all users")
    return await get_all_users()


# --- Organization member routes ---

@router.get("/organizations/{org_id}/users")
async def list_org_users(org_id: str, user: dict = Depends(get_current_user)):
    return await get_organization_users(org_id)


@router.post("/organizations/{org_id}/users")
async def add_org_member(org_id: str, member: AddMemberRequest, user: dict = Depends(get_current_user)):
    await add_user_to_organization(member.email, org_id, member.role)
    return {"status": "added", "email": member.email, "role": member.role}


@router.put("/organizations/{org_id}/users/{user_id}")
async def update_member(org_id: str, user_id: str, data: UpdateMemberRequest, user: dict = Depends(get_current_user)):
    await update_org_member_role(org_id, user_id, data.role, data.name, data.status)
    return {"status": "updated", "user_id": user_id, "role": data.role, "name": data.name, "member_status": data.status}


@router.delete("/organizations/{org_id}/users/{user_id}")
async def remove_member(org_id: str, user_id: str, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], org_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to manage this organization")
    await remove_user_from_organization(org_id, user_id)
    return {"status": "removed", "user_id": user_id}


@router.put("/projects/{project_id}/users/{user_id}")
async def update_project_member(project_id: str, user_id: str, data: UpdateMemberRequest, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], project_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to manage this project")
    await update_project_member_role(project_id, user_id, data.role, data.name, data.status)
    return {"status": "updated", "user_id": user_id, "role": data.role, "name": data.name, "member_status": data.status}


@router.delete("/projects/{project_id}/users/{user_id}")
async def remove_project_member_endpoint(project_id: str, user_id: str, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], project_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to manage this project")
    await remove_project_member(project_id, user_id)
    return {"status": "removed", "user_id": user_id}


@router.put("/themes/{theme_id}/users/{user_id}")
async def update_theme_member(theme_id: str, user_id: str, data: UpdateMemberRequest, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], theme_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to manage this theme")
    await update_theme_member_role(theme_id, user_id, data.role, data.name, data.status)
    return {"status": "updated", "user_id": user_id, "role": data.role, "name": data.name, "member_status": data.status}


@router.delete("/themes/{theme_id}/users/{user_id}")
async def remove_theme_member_endpoint(theme_id: str, user_id: str, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], theme_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to manage this theme")
    await remove_theme_member(theme_id, user_id)
    return {"status": "removed", "user_id": user_id}


# --- Invite routes ---

@router.post("/invites")
async def create_new_invite(invite: InviteRequest, user: dict = Depends(get_current_user)):
    user_email = user.get("email")
    if not user_email:
        raise HTTPException(status_code=401, detail="User not authenticated")

    existing_user = await get_user_by_email(invite.email)
    if existing_user:
        can_add = await check_permission(user["id"], invite.entity_id, Role.ADMIN)
        if not can_add:
            raise HTTPException(status_code=403, detail="Not authorized to add members")
        await add_user_to_organization(invite.email, invite.entity_id, invite.role)
        return {"status": "added", "message": f"User {invite.email} added directly."}
    else:
        try:
            result = await create_invite(
                inviter_id=user["id"],
                target_email=invite.email,
                entity_id=invite.entity_id,
                role=Role(invite.role),
                expires_in_days=invite.expires_in_days or 7,
                redirect_url=invite.redirect_url
            )
            return {"status": "invited", "invite": result}
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/invites/accept")
async def accept_invite_endpoint(data: InviteAcceptRequest, user: dict = Depends(get_current_user)):
    user_email = user.get("email")
    if not user_email:
        raise HTTPException(status_code=401, detail="User not authenticated")
    try:
        result = await accept_invite(data.code, user["id"], user_email)
        return result
    except Exception as e:
        logger.error(f"Error accepting invite: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/organizations/{org_id}/invites")
async def list_org_invites(org_id: str, user: dict = Depends(get_current_user)):
    can_view = await check_permission(user["id"], org_id, Role.ADMIN)
    if not can_view:
        raise HTTPException(status_code=403, detail="Not authorized to view invites")
    return await get_pending_invites(org_id)


@router.get("/projects/{project_id}/invites")
async def list_project_invites(project_id: str, user: dict = Depends(get_current_user)):
    can_view = await check_permission(user["id"], project_id, Role.ADMIN)
    if not can_view:
        raise HTTPException(status_code=403, detail="Not authorized to view invites")
    return await get_pending_invites(project_id)


@router.get("/themes/{theme_id}/invites")
async def list_theme_invites(theme_id: str, user: dict = Depends(get_current_user)):
    can_view = await check_permission(user["id"], theme_id, Role.ADMIN)
    if not can_view:
        raise HTTPException(status_code=403, detail="Not authorized to view invites")
    return await get_pending_invites(theme_id)
