from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel
import logging

from app.auth import get_current_user
from app.models.domain import Role
from app.db.crud import (
    get_projects, create_project, get_project_users, check_permission,
    update_project, archive_project,
    create_conversation_thread, get_threads_by_target,
)
from app.db.issues import (
    create_issue_with_designspace, get_issue, update_issue, archive_issue,
    get_issues_by_project,
)
from app.db.designspace import (
    get_designspace_with_issue,
    get_designspace_members,
    add_designspace_member,
    update_designspace_member_role,
    remove_designspace_member,
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


class IssueCreate(BaseModel):
    name: str
    description: Optional[str] = None


class IssueUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class DesignSpaceUpdate(BaseModel):
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


@router.get("/projects/{project_id}/issues")
async def list_issues(project_id: str, user: dict = Depends(get_current_user)):
    return await get_issues_by_project(project_id, user["id"])


@router.post("/projects/{project_id}/issues")
async def create_new_issue(project_id: str, issue: IssueCreate, user: dict = Depends(get_current_user)):
    result = await create_issue_with_designspace(project_id, issue.name, issue.description, owner_id=user["id"])
    return {"id": result["issue_id"], "ds_id": result["ds_id"], "name": issue.name}


@router.get("/projects/{project_id}/users")
async def list_project_users(project_id: str, user: dict = Depends(get_current_user)):
    return await get_project_users(project_id)


# --- Issue routes ---

@router.patch("/issues/{issue_id}")
async def update_issue_endpoint(issue_id: str, data: IssueUpdate, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], issue_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to edit this issue")
    await update_issue(issue_id, data.name, data.description)
    return {"status": "updated"}


@router.delete("/issues/{issue_id}")
async def archive_issue_endpoint(issue_id: str, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], issue_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to archive this issue")
    await archive_issue(issue_id)
    return {"status": "archived"}


@router.get("/issues/{issue_id}/designspace")
async def get_issue_designspace(issue_id: str, user: dict = Depends(get_current_user)):
    issue = await get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue niet gevonden")
    from app.db.utils import get_driver
    driver = get_driver()

    def _get_ds():
        with driver.session() as session:
            record = session.run(
                "MATCH (i:Issue {id: $id})-[:isAddressedInDesignSpace]->(ds:DesignSpace) RETURN ds.id AS ds_id",
                {"id": issue_id},
            ).single()
            return record["ds_id"] if record else None

    import asyncio
    ds_id = await asyncio.to_thread(_get_ds)
    if not ds_id:
        raise HTTPException(status_code=404, detail="DesignSpace niet gevonden voor dit issue")
    result = await get_designspace_with_issue(ds_id)
    if not result:
        raise HTTPException(status_code=404, detail="DesignSpace niet gevonden")
    return result


# --- DesignSpace routes ---

@router.get("/designspace/{ds_id}")
async def read_designspace(ds_id: str, user: dict = Depends(get_current_user)):
    result = await get_designspace_with_issue(ds_id)
    if not result:
        raise HTTPException(status_code=404, detail="DesignSpace niet gevonden")
    return result


@router.patch("/designspace/{ds_id}")
async def update_designspace_endpoint(ds_id: str, data: DesignSpaceUpdate, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], ds_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to edit this designspace")
    ds = await get_designspace_with_issue(ds_id)
    if not ds or not ds.get("issue_id"):
        raise HTTPException(status_code=404, detail="DesignSpace of gekoppeld Issue niet gevonden")
    await update_issue(ds["issue_id"], data.name, data.description)
    return {"status": "updated"}


@router.delete("/designspace/{ds_id}")
async def archive_designspace_endpoint(ds_id: str, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], ds_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to archive this designspace")
    ds = await get_designspace_with_issue(ds_id)
    if not ds or not ds.get("issue_id"):
        raise HTTPException(status_code=404, detail="DesignSpace of gekoppeld Issue niet gevonden")
    await archive_issue(ds["issue_id"])
    return {"status": "archived"}


@router.post("/designspace/{ds_id}/threads")
async def create_ds_thread(ds_id: str, thread: ThreadCreate, user: dict = Depends(get_current_user)):
    tid = await create_conversation_thread(ds_id, thread.topic)
    return {"id": tid, "topic": thread.topic}


@router.get("/designspace/{ds_id}/threads")
async def list_ds_threads(ds_id: str, user: dict = Depends(get_current_user)):
    return await get_threads_by_target(ds_id)


@router.get("/designspace/{ds_id}/members")
async def list_ds_members(ds_id: str, user: dict = Depends(get_current_user)):
    return await get_designspace_members(ds_id)


@router.post("/designspace/{ds_id}/members")
async def invite_ds_member(ds_id: str, data: MemberInvite, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], ds_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to invite members to this designspace")
    await add_designspace_member(ds_id, data.email, data.role)
    return {"status": "invited"}


@router.patch("/designspace/{ds_id}/members/{member_id}")
async def update_ds_member(ds_id: str, member_id: str, data: RoleUpdate, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], ds_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to manage members in this designspace")
    await update_designspace_member_role(ds_id, member_id, data.role)
    return {"status": "role updated"}


@router.delete("/designspace/{ds_id}/members/{member_id}")
async def remove_ds_member(ds_id: str, member_id: str, user: dict = Depends(get_current_user)):
    if not await check_permission(user["id"], ds_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to remove members from this designspace")
    await remove_designspace_member(ds_id, member_id)
    return {"status": "removed"}
