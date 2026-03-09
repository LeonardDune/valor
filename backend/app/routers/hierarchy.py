from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel
import logging

from app.auth import get_current_user
from app.models.domain import Role
from app.db.crud import (
    get_projects, create_project, get_project_themes, create_theme,
    get_project_users, get_theme_users, check_permission,
    update_project, archive_project,
    update_theme, archive_theme,
    create_theme_version, get_theme_versions_by_theme,
    get_theme_version, update_theme_version, archive_theme_version,
    get_theme_version_users, add_user_to_theme_version,
    update_theme_version_member_role, delete_theme_version_member,
    create_conversation_thread, get_threads_by_target,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class ProjectCreate(BaseModel):
    organization_id: str
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ThemeCreate(BaseModel):
    project_id: str
    name: str
    description: Optional[str] = None


class ThemeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ThemeVersionCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ThemeVersionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class MemberInvite(BaseModel):
    email: str
    role: str


class RoleUpdate(BaseModel):
    role: str


class ThreadCreate(BaseModel):
    topic: str


# --- Project routes ---

@router.get("/projects")
async def list_projects(organization_id: str, user: dict = Depends(get_current_user)):
    return await get_projects(organization_id, user["id"])


@router.post("/projects")
async def create_new_project(project: ProjectCreate, user: dict = Depends(get_current_user)):
    pid = await create_project(project.name, project.organization_id, project.description, owner_id=user["id"])
    return {"id": pid, "name": project.name}


@router.patch("/projects/{project_id}")
async def update_project_endpoint(project_id: str, data: ProjectUpdate, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], project_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to edit this project")
    await update_project(project_id, data.name, data.description)
    return {"status": "updated"}


@router.delete("/projects/{project_id}")
async def archive_project_endpoint(project_id: str, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], project_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to archive this project")
    await archive_project(project_id)
    return {"status": "archived"}


@router.get("/projects/{project_id}/themes")
async def list_themes(project_id: str, user: dict = Depends(get_current_user)):
    return await get_project_themes(project_id, user["id"])


@router.post("/projects/{project_id}/themes")
async def create_new_theme(project_id: str, theme: ThemeCreate, user: dict = Depends(get_current_user)):
    tid = await create_theme(project_id, theme.name, theme.description, owner_id=user["id"])
    return {"id": tid, "name": theme.name}


@router.get("/projects/{project_id}/users")
async def list_project_users(project_id: str, user: dict = Depends(get_current_user)):
    return await get_project_users(project_id)


# --- Theme routes ---

@router.get("/themes/{theme_id}/users")
async def list_theme_users(theme_id: str, user: dict = Depends(get_current_user)):
    return await get_theme_users(theme_id)


@router.patch("/themes/{theme_id}")
async def update_theme_endpoint(theme_id: str, data: ThemeUpdate, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], theme_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to edit this theme")
    await update_theme(theme_id, data.name, data.description)
    return {"status": "updated"}


@router.delete("/themes/{theme_id}")
async def archive_theme_endpoint(theme_id: str, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], theme_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to archive this theme")
    await archive_theme(theme_id)
    return {"status": "archived"}


@router.post("/themes/{theme_id}/versions")
@router.post("/themes/{theme_id}/spaces", deprecated=True)
async def create_new_theme_version(theme_id: str, version: ThemeVersionCreate, user: dict = Depends(get_current_user)):
    sid = await create_theme_version(theme_id, version.name, version.description, owner_id=user["id"])
    return {"id": sid, "name": version.name}


@router.get("/themes/{theme_id}/versions")
@router.get("/themes/{theme_id}/spaces", deprecated=True)
async def read_theme_versions(theme_id: str, user: dict = Depends(get_current_user)):
    return await get_theme_versions_by_theme(theme_id, user_id=user["id"])


@router.get("/themes/{theme_id}/active-version")
async def read_theme_active_version(theme_id: str, user: dict = Depends(get_current_user)):
    from app.db.crud import get_theme_active_version
    version = await get_theme_active_version(theme_id, user_id=user["id"])
    if not version:
        raise HTTPException(status_code=404, detail="Active Theme Version not found or access denied")
    return version


# --- Version / Space routes ---

@router.get("/versions/{version_id}")
@router.get("/spaces/{version_id}", deprecated=True)
async def read_theme_version_endpoint(version_id: str, user: dict = Depends(get_current_user)):
    version = await get_theme_version(version_id, user_id=user["id"])
    if not version:
        raise HTTPException(status_code=404, detail="Theme Version not found")
    return version


@router.patch("/versions/{version_id}")
@router.patch("/spaces/{version_id}", deprecated=True)
async def update_theme_version_endpoint(version_id: str, name: str, description: Optional[str] = None, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], version_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to edit this version")
    await update_theme_version(version_id, name, description)
    return {"status": "updated"}


@router.delete("/versions/{version_id}")
@router.delete("/spaces/{version_id}", deprecated=True)
async def archive_theme_version_endpoint(version_id: str, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], version_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to archive this version")
    await archive_theme_version(version_id)
    return {"status": "archived"}


@router.post("/versions/{version_id}/threads")
@router.post("/spaces/{version_id}/threads", deprecated=True)
async def create_new_thread(version_id: str, thread: ThreadCreate, user: dict = Depends(get_current_user)):
    tid = await create_conversation_thread(version_id, thread.topic)
    return {"id": tid, "topic": thread.topic}


@router.get("/versions/{version_id}/threads")
@router.get("/spaces/{version_id}/threads", deprecated=True)
async def list_version_threads(version_id: str, user: dict = Depends(get_current_user)):
    return await get_threads_by_target(version_id)


@router.get("/versions/{version_id}/members")
@router.get("/spaces/{version_id}/members", deprecated=True)
async def list_version_members(version_id: str, user: dict = Depends(get_current_user)):
    return await get_theme_version_users(version_id)


@router.post("/versions/{version_id}/members")
@router.post("/spaces/{version_id}/members", deprecated=True)
async def invite_version_member(version_id: str, data: MemberInvite, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], version_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to invite members to this version")
    await add_user_to_theme_version(data.email, version_id, data.role)
    return {"status": "invited"}


@router.patch("/versions/{version_id}/members/{user_id}")
@router.patch("/spaces/{version_id}/members/{user_id}", deprecated=True)
async def update_version_member(version_id: str, user_id: str, data: RoleUpdate, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], version_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to manage members in this version")
    await update_theme_version_member_role(version_id, user_id, data.role)
    return {"status": "role updated"}


@router.delete("/versions/{version_id}/members/{user_id}")
@router.delete("/spaces/{version_id}/members/{user_id}", deprecated=True)
async def remove_version_member_endpoint(version_id: str, user_id: str, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], version_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to remove members from this version")
    await delete_theme_version_member(version_id, user_id)
    return {"status": "removed"}
