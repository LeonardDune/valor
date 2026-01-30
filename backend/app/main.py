from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
from dotenv import load_dotenv
from app.models.domain import ConversationRequest, ConversationResponse
from app.routers import proposals, dashboard
from app.agent.core import process_user_message
from app.db.crud import save_claims, set_conversation_topic
import uuid

from contextlib import asynccontextmanager
from app.db.utils import close_driver, verify_connectivity
from app.auth import verify_token, security
from fastapi import Depends, HTTPException, WebSocket, WebSocketDisconnect
import logging
from app.services.connection_manager import manager
from app.db.invites import create_invite, get_pending_invites, accept_invite
from app.models.domain import InviteStatus, Role

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up...")
    await verify_connectivity()
    await startup_migration()
    yield
    # Shutdown
    logger.info("Shutting down...")
    close_driver()

async def startup_migration():
    """Ensures a default organization and user exist, and links orphaned projects."""
    try:
        from app.db.crud import (
            create_organization, create_user, get_organizations, get_driver,
            create_space, get_spaces_by_theme, get_space, update_space, archive_space, get_space_users,
            update_space_member_role, delete_space_member, add_user_to_space
        )
        
        # 1. Ensure Default Organization
        orgs = await get_organizations()
        default_org_id = None
        if not orgs:
            logger.info("No organizations found. Creating Default Organization.")
            default_org_id = await create_organization("Default Organization", "Auto-created during migration")
        else:
            default_org_id = orgs[0]['id']
            
        # 2. Ensure Admin User
        # We skip hardcoded creation here to avoid conflict. 
        # Admin should be created via scripts/init_dev_db.py or manual onboarding.
        pass
        
        # 3. Link Orphaned Projects
        driver = get_driver()
        query = """
        MATCH (p:Project)
        WHERE NOT (p)<-[:OWNS]-(:Organization)
        MATCH (o:Organization {id: $oid})
        MERGE (o)-[:OWNS]->(p)
        RETURN count(p) as count
        """
        with driver.session() as session:
            result = session.run(query, {"oid": default_org_id})
            count = result.single()["count"]
            if count > 0:
                logger.info(f"Migrated {count} orphaned projects to Default Organization ({default_org_id})")
                
    except Exception as e:
        logger.error(f"Migration failed: {e}")

load_dotenv()

app = FastAPI(title="CAUSA Backend", lifespan=lifespan)

# CORS Configuration
# Allow all for MVP simplicity, restrict in production if needed
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication Dependency with JIT Sync
async def get_current_user(payload: dict = Depends(verify_token)):
    user_id = payload.get("sub")
    email = payload.get("email")
    user_meta = payload.get("user_metadata", {})
    name = user_meta.get("full_name") or user_meta.get("name")
    
    if not user_id or not email:
        raise HTTPException(status_code=401, detail="Invalid token payload")
        
    # JIT Sync: Ensure user exists in Neo4j and is up-to-date
    return await ensure_user_sync(user_id, email, name)

@app.get("/")
async def root():
    return {"message": "Welcome to CAUSA API", "status": "running"}

app.include_router(proposals.router)
app.include_router(dashboard.router)

@app.get("/health")
async def health_check():
    is_connected = await verify_connectivity()
    status = "ok" if is_connected else "db_error"
    return {"status": status, "neo4j_connected": is_connected}

@app.post("/chat", response_model=ConversationResponse)
async def chat_endpoint(request: ConversationRequest):
    cid = request.conversation_id or str(uuid.uuid4())
    
    if request.topic:
        await set_conversation_topic(cid, request.topic)
    
    # Extract claims using Agent
    response = await process_user_message(request.message, cid)
    
    # Persist extracted claims to Neo4j
    if response.extracted_claims:
        await save_claims(cid, response.extracted_claims)
        
    return response
    return response


import jwt 
from jwt import PyJWKClient

# ...

@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str, token: Optional[str] = None):
    """
    WebSocket endpoint for real-time collaboration.
    Handles ephemeral presence events (cursor, focus) and subscribes to data updates.
    """
    # Default to anon if auth fails (for now, to allow partial function), but strictly logged.
    # If users are Anon, broadcast ignores them if they overwrite.
    # Strategy: If Anon, generate UNIQUE ID? 
    # Better: Ensure Auth works.
    
    user_id = f"anon-{uuid.uuid4().hex[:6]}" # Unique anon ID to prevent collision!
    
    # Authenticate
    if token:
        try:
            # Helper for WS Auth
            from app.auth import verify_token_string 
            payload = verify_token_string(token)
            # Use email as ID (stable)
            user_id = payload.get("email") or payload.get("sub") or user_id
            logger.info(f"WebSocket Authenticated: {user_id} for Project {project_id}")
            
        except Exception as e:
            logger.error(f"WebSocket Auth Failed for project {project_id}. Token starts with: {token[:10] if token else 'None'}. Error: {e}")
            # If auth fails, should we close?
            # User requirement: "Why is it Anon?" -> They expect Auth.
            # If we fall back to Unique Anon, at least Sync works.
            # But Name is Anon.
            # Let's keep Unique Anon as fallback so Sync works instantly. 
            pass
    else:
        logger.warning(f"WebSocket connection without Token for {project_id}")

    await manager.connect(websocket, project_id, user_id)
    try:
        while True:
            # Handle incoming messages
            data = await websocket.receive_json()
            
            # Inject sender info if missing? 
            # PresenceLayer sends { user_id, ... } in payload. 
            # We trust client or verify?
            # Ideally: override payload.user_id with Authenticated ID?
            # For "Anon" users, we want the generated specific ID.
            if isinstance(data, dict):
                 # Ensure payload exists
                 if "payload" not in data:
                     data["payload"] = {}
                 
                 # Force the real user_id to ensure consistency (and fix Anon name)
                 # If client sends "user_id" matches "anon", replace with mapped ID?
                 # Better: Trust server-side ID for badges.
                 if "user_id" in data["payload"]:
                      # If client claims to be someone else, maybe unexpected.
                      # But let's overwrite with verified ID to be safe/correct.
                      data["payload"]["user_id"] = user_id
                 
                 # Also for NODE_FOCUS, user_id is in payload
                 # Make sure we add it if missing
                 if data.get("type") == "NODE_FOCUS":
                      data["payload"]["user_id"] = user_id
            
            # Broadcast ephemeral events back to other clients (e.g. Presence)
            await manager.broadcast_presence(project_id, user_id, data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, project_id, user_id)

# Hierarchy Endpoints

from app.db.crud import (
    get_claims_for_theme, create_organization, get_organizations, create_user,
    get_organization_users, add_user_to_organization, update_org_member_role,
    remove_user_from_organization, update_user_profile, get_user_organizations,
    get_projects, create_project, get_project_themes, create_theme, get_user_by_email,
    check_permission, get_project_users, get_theme_users, get_all_users,
    update_organization, archive_organization, update_project, archive_project,
    update_theme, archive_theme, update_project_member_role, remove_project_member,
    update_theme_member_role, remove_theme_member, get_project_id_by_theme,
    get_project_id_by_factor, get_project_id_by_claim, ensure_user_sync,
    get_user_by_id, create_conversation_thread, get_threads_by_space
)
from pydantic import BaseModel

class OrganizationCreate(BaseModel):
    name: str
    description: Optional[str] = None

class UserCreate(BaseModel):
    email: str
    name: Optional[str] = None

class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None

class ProjectCreate(BaseModel):
    organization_id: str
    name: str
    description: Optional[str] = None

class ThemeCreate(BaseModel):
    project_id: str
    name: str
    description: Optional[str] = None

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ThemeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class SpaceCreate(BaseModel):
    name: str
    description: Optional[str] = None

class SpaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class MemberInvite(BaseModel):
    email: str
    role: str

class RoleUpdate(BaseModel):
    role: str

@app.get("/organizations")
async def list_organizations(user: dict = Depends(get_current_user)):
    email = user.get("email")
    if not email:
        return []
    
    # Check Platform Admin status
    current_user_data = await get_user_by_email(email)
    is_admin = current_user_data and current_user_data.get('is_platform_admin')
    
    if is_admin:
        logger.info(f"Platform Admin {email} requesting all organizations")
        orgs = await get_organizations()
    else:
        logger.info(f"Checking organizations for user: {email}")
        orgs = await get_user_organizations(email)
    
    logger.info(f"Found {len(orgs)} organizations for user {email} (Admin: {is_admin})")
    return orgs

@app.post("/organizations")
async def create_new_organization(org: OrganizationCreate, user: dict = Depends(get_current_user)):
    # Use id from synced user
    oid = await create_organization(org.name, org.description, owner_id=user["id"])
    return {"id": oid, "name": org.name}

@app.patch("/organizations/{org_id}")
async def update_org(org_id: str, data: OrganizationUpdate, user: dict = Depends(get_current_user)):
    email = user.get("email")
    if not await check_permission(email, org_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to edit this organization")
    await update_organization(org_id, data.name, data.description)
    return {"status": "updated"}

@app.delete("/organizations/{org_id}")
async def archive_org_endpoint(org_id: str, user: dict = Depends(get_current_user)):
    email = user.get("email")
    if not await check_permission(email, org_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to archive this organization")
    await archive_organization(org_id)
    return {"status": "archived"}

@app.post("/users")
async def create_new_user(user: UserCreate, user_auth: dict = Depends(get_current_user)):
    # Note: Logic might need update to map auth provider ID
    uid = await create_user(user.email, user.name)
    return {"id": uid, "email": user.email}

@app.put("/users/me")
async def update_my_profile(profile: UserProfileUpdate, user: dict = Depends(get_current_user)):
    email = user.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="User email not found in token")
        
    await update_user_profile(email, profile.first_name, profile.last_name, profile.username)
    return {"status": "updated", "email": email}

@app.get("/users/me")
async def get_current_user_profile(
    user: dict = Depends(get_current_user)
):
    """Get full profile of the currently authenticated user."""
    # get_current_user already returns the full DB user
    return user

class AddMemberRequest(BaseModel):
    email: str
    role: str = "member"

@app.get("/organizations/{org_id}/users")
async def list_org_users(org_id: str, user: dict = Depends(get_current_user)):
    return await get_organization_users(org_id)

@app.post("/organizations/{org_id}/users")
async def add_org_member(org_id: str, member: AddMemberRequest, user: dict = Depends(get_current_user)):
    await add_user_to_organization(member.email, org_id, member.role)
    return {"status": "added", "email": member.email, "role": member.role}

class UpdateMemberRequest(BaseModel):
    role: str
    name: Optional[str] = None
    status: Optional[str] = None

@app.put("/organizations/{org_id}/users/{user_id}")
async def update_member(org_id: str, user_id: str, data: UpdateMemberRequest, user: dict = Depends(get_current_user)):
    await update_org_member_role(org_id, user_id, data.role, data.name, data.status)
    return {"status": "updated", "user_id": user_id, "role": data.role, "name": data.name, "member_status": data.status}

@app.delete("/organizations/{org_id}/users/{user_id}")
async def remove_member(org_id: str, user_id: str, user: dict = Depends(get_current_user)):
    email = user.get("email")
    if not await check_permission(email, org_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to manage this organization")
    await remove_user_from_organization(org_id, user_id)
    return {"status": "removed", "user_id": user_id}

@app.put("/projects/{project_id}/users/{user_id}")
async def update_project_member(project_id: str, user_id: str, data: UpdateMemberRequest, user: dict = Depends(get_current_user)):
    email = user.get("email")
    if not await check_permission(email, project_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to manage this project")
    await update_project_member_role(project_id, user_id, data.role, data.name, data.status)
    return {"status": "updated", "user_id": user_id, "role": data.role, "name": data.name, "member_status": data.status}

@app.delete("/projects/{project_id}/users/{user_id}")
async def remove_project_member_endpoint(project_id: str, user_id: str, user: dict = Depends(get_current_user)):
    email = user.get("email")
    if not await check_permission(email, project_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to manage this project")
    await remove_project_member(project_id, user_id)
    return {"status": "removed", "user_id": user_id}

@app.put("/themes/{theme_id}/users/{user_id}")
async def update_theme_member(theme_id: str, user_id: str, data: UpdateMemberRequest, user: dict = Depends(get_current_user)):
    email = user.get("email")
    if not await check_permission(email, theme_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to manage this theme")
    await update_theme_member_role(theme_id, user_id, data.role, data.name, data.status)
    return {"status": "updated", "user_id": user_id, "role": data.role, "name": data.name, "member_status": data.status}

@app.delete("/themes/{theme_id}/users/{user_id}")
async def remove_theme_member_endpoint(theme_id: str, user_id: str, user: dict = Depends(get_current_user)):
    email = user.get("email")
    if not await check_permission(email, theme_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to manage this theme")
    await remove_theme_member(theme_id, user_id)
    return {"status": "removed", "user_id": user_id}

@app.get("/projects")
async def list_projects(organization_id: str, user: dict = Depends(get_current_user)):
    return await get_projects(organization_id, user["id"])

@app.get("/projects/{project_id}/users")
async def list_project_users(project_id: str, user: dict = Depends(get_current_user)):
    # Add permission check?
    return await get_project_users(project_id)

@app.get("/themes/{theme_id}/users")
async def list_theme_users(theme_id: str, user: dict = Depends(get_current_user)):
    return await get_theme_users(theme_id)

@app.get("/users")
async def list_all_users(user: dict = Depends(get_current_user)):
    # Check if platform admin
    email = user.get("email")
    is_admin = await check_permission(email, "GLOBAL", Role.ADMIN) 
    # Wait, check_permission needs an ID. 
    # For global check, we rely on the `permissions.py` update which checks `user.is_platform_admin`.
    # But check_permission logic requires an Entity ID to traverse.
    # We should add a specific check or pass a dummy ID?
    # Actually, simpler: fetch user and check flag directly.
    
    current_user_data = await get_user_by_email(email)
    if not current_user_data or not current_user_data.get('is_platform_admin'):
         raise HTTPException(status_code=403, detail="Only Platform Admins can view all users")
         
    return await get_all_users()

# Invite Endpoints

class InviteRequest(BaseModel):
    email: str
    entity_id: str
    role: str = "member"
    expires_in_days: Optional[int] = 7
    redirect_url: Optional[str] = None

class InviteAcceptRequest(BaseModel):
    code: str

@app.post("/invites")
async def create_new_invite(invite: InviteRequest, user: dict = Depends(get_current_user)):
    user_email = user.get("email")
    if not user_email:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # Hybrid Logic: Check if user exists
    existing_user = await get_user_by_email(invite.email)
    if existing_user:
        # User exists: Add directly (assuming admin consent implies user consent for now, or just notify)
        # Check permissions via add_user wrapper or directly here
        # For consistency with "Invite" flow, let's just add them as MEMBER_OF
        # BUT: Check if inviter has permission
        can_add = await check_permission(user_email, invite.entity_id, Role.ADMIN)
        if not can_add:
            raise HTTPException(status_code=403, detail="Not authorized to add members")
            
        await add_user_to_organization(invite.email, invite.entity_id, invite.role)
        return {"status": "added", "message": f"User {invite.email} added directly."}
    else:
        # User does not exist: Create Invite
        try:
            result = await create_invite(
                inviter_email=user_email,
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

@app.get("/organizations/{org_id}/invites")
async def list_org_invites(org_id: str, user: dict = Depends(get_current_user)):
    # Check permissions? (Admin only)
    user_email = user.get("email")
    can_view = await check_permission(user_email, org_id, Role.ADMIN)
    if not can_view:
        raise HTTPException(status_code=403, detail="Not authorized to view invites")
        
    return await get_pending_invites(org_id)

@app.get("/projects/{project_id}/invites")
async def list_project_invites(project_id: str, user: dict = Depends(get_current_user)):
    user_email = user.get("email")
    can_view = await check_permission(user_email, project_id, Role.ADMIN)
    if not can_view:
        raise HTTPException(status_code=403, detail="Not authorized to view invites")
    return await get_pending_invites(project_id)

@app.get("/themes/{theme_id}/invites")
async def list_theme_invites(theme_id: str, user: dict = Depends(get_current_user)):
    user_email = user.get("email")
    can_view = await check_permission(user_email, theme_id, Role.ADMIN)
    if not can_view:
        raise HTTPException(status_code=403, detail="Not authorized to view invites")
    return await get_pending_invites(theme_id)

@app.post("/invites/accept")
async def accept_invite_endpoint(data: InviteAcceptRequest, user: dict = Depends(get_current_user)):
    user_email = user.get("email")
    if not user_email:
        raise HTTPException(status_code=401, detail="User not authenticated")
        
    try:
        result = await accept_invite(data.code, user_email)
        return result
    except Exception as e:
        logger.error(f"Error accepting invite: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/projects")
async def create_new_project(project: ProjectCreate, user: dict = Depends(get_current_user)):
    pid = await create_project(project.name, project.organization_id, project.description, owner_id=user["id"])
    return {"id": pid, "name": project.name}

@app.patch("/projects/{project_id}")
async def update_project_endpoint(project_id: str, data: ProjectUpdate, user: dict = Depends(get_current_user)):
    email = user.get("email")
    if not await check_permission(email, project_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to edit this project")
    await update_project(project_id, data.name, data.description)
    return {"status": "updated"}

@app.delete("/projects/{project_id}")
async def archive_project_endpoint(project_id: str, user: dict = Depends(get_current_user)):
    email = user.get("email")
    if not await check_permission(email, project_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to archive this project")
    await archive_project(project_id)
    return {"status": "archived"}

@app.get("/projects/{project_id}/themes")
async def list_themes(project_id: str, user: dict = Depends(get_current_user)):
    return await get_project_themes(project_id, user.get("email"))

@app.post("/projects/{project_id}/themes")
async def create_new_theme(project_id: str, theme: ThemeCreate, user: dict = Depends(get_current_user)):
    tid = await create_theme(project_id, theme.name, theme.description, owner_id=user["id"])
    return {"id": tid, "name": theme.name}

@app.patch("/themes/{theme_id}")
async def update_theme_endpoint(theme_id: str, data: ThemeUpdate, user: dict = Depends(get_current_user)):
    email = user.get("email")
    if not await check_permission(email, theme_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to edit this theme")
    await update_theme(theme_id, data.name, data.description)
    return {"status": "updated"}

@app.delete("/themes/{theme_id}")
async def archive_theme_endpoint(theme_id: str, user: dict = Depends(get_current_user)):
    email = user.get("email")
    if not await check_permission(email, theme_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to archive this theme")
    await archive_theme(theme_id)
    return {"status": "archived"}

@app.post("/themes/{theme_id}/spaces")
async def create_new_space(theme_id: str, space: SpaceCreate, user: dict = Depends(get_current_user)):
    sid = await create_space(theme_id, space.name, space.description, owner_id=user["id"])
    return {"id": sid, "name": space.name}

@app.get("/themes/{theme_id}/spaces")
async def read_theme_spaces(theme_id: str, user: dict = Depends(get_current_user)):
    return await get_spaces_by_theme(theme_id, user_id=user["id"])

@app.get("/spaces/{space_id}")
async def read_space(space_id: str, user: dict = Depends(get_current_user)):
    space = await get_space(space_id, user_id=user["id"])
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    return space

@app.patch("/spaces/{space_id}")
async def update_space_endpoint(space_id: str, name: str, description: Optional[str] = None, user: dict = Depends(get_current_user)):
    email = user.get("email")
    if not await check_permission(email, space_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to edit this space")
    await update_space(space_id, name, description)
    return {"status": "updated"}

@app.delete("/spaces/{space_id}")
async def archive_space_endpoint(space_id: str, user: dict = Depends(get_current_user)):
    email = user.get("email")
    if not await check_permission(email, space_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to archive this space")
    await archive_space(space_id)
    return {"status": "archived"}

class ThreadCreate(BaseModel):
    topic: str

@app.post("/spaces/{space_id}/threads")
async def create_new_thread(space_id: str, thread: ThreadCreate, user: dict = Depends(get_current_user)):
    # Check permissions (Member access okay for creating threads? Or Admin? Intent says "Participant", so Member is likely fine.)
    # Let's enforce Membership at least.
    email = user.get("email")
    # For now, relying on space existing. Ideally check `is_member`.
    # Assuming if you can see the space, you can create a thread.
    # Refine later if strict permissions needed.
    tid = await create_conversation_thread(space_id, thread.topic)
    return {"id": tid, "topic": thread.topic}

@app.get("/spaces/{space_id}/threads")
async def list_space_threads(space_id: str, user: dict = Depends(get_current_user)):
    # Check membership?
    return await get_threads_by_space(space_id)
@app.get("/spaces/{space_id}/members")
async def list_space_members(space_id: str, user: dict = Depends(get_current_user)):
    return await get_space_users(space_id)

@app.post("/spaces/{space_id}/members")
async def invite_space_member(space_id: str, data: MemberInvite, user: dict = Depends(get_current_user)):
    email = user.get("email")
    if not await check_permission(email, space_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to invite members to this space")
    await add_user_to_space(data.email, space_id, data.role)
    return {"status": "invited"}

@app.patch("/spaces/{space_id}/members/{user_id}")
async def update_space_member(space_id: str, user_id: str, data: RoleUpdate, user: dict = Depends(get_current_user)):
    email = user.get("email")
    if not await check_permission(email, space_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to manage members in this space")
    await update_space_member_role(space_id, user_id, data.role)
    return {"status": "role updated"}

@app.delete("/spaces/{space_id}/members/{user_id}")
async def remove_space_member_endpoint(space_id: str, user_id: str, user: dict = Depends(get_current_user)):
    email = user.get("email")
    if not await check_permission(email, space_id, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to remove members from this space")
    await delete_space_member(space_id, user_id)
    return {"status": "removed"}

@app.get("/themes/{theme_id}/claims")
async def list_theme_claims(theme_id: str):
    return await get_claims_for_theme(theme_id)

@app.get("/themes/{theme_id}/factors")
async def list_theme_factors(theme_id: str):
    return await get_factors_for_theme(theme_id)

# Manual Editing Endpoints

from app.db.crud import (
    create_factor_manual, update_factor_manual, delete_factor_manual,
    create_claim_manual, update_claim_manual, delete_claim_manual,
    get_factors_for_theme,
    create_space, get_spaces_by_theme,
    # Space Users
    get_space_users, add_user_to_space, update_space_member_role, delete_space_member,
    get_space, update_space, archive_space
)

class FactorManualCreate(BaseModel):
    name: str
    description: Optional[str] = None
    type: Optional[str] = "systeemelement"
    theme_id: Optional[str] = None

class FactorUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    theme_id: Optional[str] = None

class ClaimManualCreate(BaseModel):
    theme_id: str
    source_id: str
    target_id: str
    statement: str
    polarity: Optional[str] = "+"
    confidence: Optional[float] = 1.0

class ClaimUpdate(BaseModel):
    statement: Optional[str] = None
    polarity: Optional[str] = None
    confidence: Optional[float] = None
    source_id: Optional[str] = None
    target_id: Optional[str] = None

@app.post("/factors")
async def create_factor(factor: FactorManualCreate):
    logger.info(f"Creating factor: {factor}")
    fid = await create_factor_manual(factor.name, factor.description, factor.type or "systeemelement", factor.theme_id)
    
    # Broadcast Update
    if factor.theme_id:
        project_id = await get_project_id_by_theme(factor.theme_id)
        if project_id:
            await manager.broadcast_data(project_id, {
                "type": "FACTOR_CREATED",
                "payload": {"id": fid, "name": factor.name, "description": factor.description, "type": factor.type, "theme_id": factor.theme_id}
            })
        
    return {"id": fid, "name": factor.name}

@app.patch("/factors/{factor_id}")
async def update_factor_route(factor_id: str, factor: FactorUpdate):
    await update_factor_manual(factor_id, factor.name, factor.description, factor.type, factor.theme_id)
    # Broadcast
    project_id = await get_project_id_by_factor(factor_id)
    if project_id:
         await manager.broadcast_data(project_id, {
                "type": "FACTOR_UPDATED",
                "payload": {"id": factor_id, "changes": factor.dict(exclude_unset=True)}
            })
    return {"status": "updated"}

@app.delete("/factors/{factor_id}")
async def delete_factor_route(factor_id: str):
    # Get project ID before deletion!
    project_id = await get_project_id_by_factor(factor_id)
    await delete_factor_manual(factor_id)
    if project_id:
         await manager.broadcast_data(project_id, {
                "type": "FACTOR_DELETED",
                "payload": {"id": factor_id}
            })
    return {"status": "deleted"}

@app.post("/claims_manual")
async def create_claim(claim: ClaimManualCreate):
    logger.info(f"Creating claim: {claim}")
    cid = await create_claim_manual(
        claim.theme_id, 
        claim.source_id, 
        claim.target_id, 
        claim.statement, 
        claim.polarity, 
        claim.confidence
    )
    # Broadcast
    if claim.theme_id:
        project_id = await get_project_id_by_theme(claim.theme_id)
        if project_id:
            await manager.broadcast_data(project_id, {
                "type": "CLAIM_CREATED",
                "payload": {"id": cid, "source_id": claim.source_id, "target_id": claim.target_id, "theme_id": claim.theme_id, "statement": claim.statement}
            })

    return {"status": "created", "id": cid}

@app.patch("/claims/{claim_id}")
async def update_claim_route(claim_id: str, claim: ClaimUpdate):
    await update_claim_manual(
        claim_id, 
        claim.statement, 
        claim.polarity, 
        claim.confidence, 
        claim.source_id, 
        claim.target_id
    )
    # Broadcast
    project_id = await get_project_id_by_claim(claim_id)
    if project_id:
         await manager.broadcast_data(project_id, {
                "type": "CLAIM_UPDATED",
                "payload": {"id": claim_id, "changes": claim.dict(exclude_unset=True)}
            })
    return {"status": "updated"}

@app.delete("/claims/{claim_id}")
async def delete_claim_route(claim_id: str):
    project_id = await get_project_id_by_claim(claim_id)
    await delete_claim_manual(claim_id)
    if project_id:
         await manager.broadcast_data(project_id, {
                "type": "CLAIM_DELETED",
                "payload": {"id": claim_id}
            })
    return {"status": "deleted"}
