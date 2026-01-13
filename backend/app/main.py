from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
from dotenv import load_dotenv
from app.models.domain import ConversationRequest, ConversationResponse
from app.agent.core import process_user_message
from app.db.crud import save_claims, set_conversation_topic
import uuid

from contextlib import asynccontextmanager
from app.db.utils import close_driver, verify_connectivity
from app.auth import get_current_user
from fastapi import Depends
import logging

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
        from app.db.crud import create_organization, create_user, get_organizations, get_driver
        
        # 1. Ensure Default Organization
        orgs = await get_organizations()
        default_org_id = None
        if not orgs:
            logger.info("No organizations found. Creating Default Organization.")
            default_org_id = await create_organization("Default Organization", "Auto-created during migration")
        else:
            default_org_id = orgs[0]['id']
            
        # 2. Ensure Admin User
        # We don't have a get_users yet, so we just try to create (merge handles duplicates)
        # Actually create_user uses MERGE on email, so it's safe.
        await create_user("admin@valor.local", "System Admin")
        
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

@app.get("/")
async def root():
    return {"message": "Welcome to CAUSA API", "status": "running"}

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

# Hierarchy Endpoints

from app.db.crud import (
    get_claims_for_theme, create_organization, get_organizations, create_user,
    get_organization_users, add_user_to_organization, update_org_member_role,
    remove_user_from_organization, update_user_profile, get_user_organizations,
    get_projects, create_project, get_project_themes, create_theme
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

@app.get("/organizations")
async def list_organizations(user: dict = Depends(get_current_user)):
    email = user.get("email")
    if not email:
        return []
    logger.info(f"Checking organizations for user: {email}")
    orgs = await get_user_organizations(email)
    logger.info(f"Found {len(orgs)} organizations for user {email}")
    return orgs

@app.post("/organizations")
async def create_new_organization(org: OrganizationCreate, user: dict = Depends(get_current_user)):
    # Use email from token to link owner
    email = user.get("email")
    oid = await create_organization(org.name, org.description, owner_email=email)
    return {"id": oid, "name": org.name}

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

@app.put("/organizations/{org_id}/users/{user_id}")
async def update_member(org_id: str, user_id: str, data: UpdateMemberRequest, user: dict = Depends(get_current_user)):
    await update_org_member_role(org_id, user_id, data.role, data.name)
    return {"status": "updated", "user_id": user_id, "role": data.role, "name": data.name}

@app.delete("/organizations/{org_id}/users/{user_id}")
async def remove_member(org_id: str, user_id: str, user: dict = Depends(get_current_user)):
    await remove_user_from_organization(org_id, user_id)
    return {"status": "removed", "user_id": user_id}

@app.get("/projects")
async def list_projects(organization_id: str, user: dict = Depends(get_current_user)):
    return await get_projects(organization_id)

@app.post("/projects")
async def create_new_project(project: ProjectCreate, user: dict = Depends(get_current_user)):
    pid = await create_project(project.name, project.organization_id, project.description)
    return {"id": pid, "name": project.name}

@app.get("/projects/{project_id}/themes")
async def list_themes(project_id: str):
    return await get_project_themes(project_id)

@app.post("/projects/{project_id}/themes")
async def create_new_theme(project_id: str, theme: ThemeCreate):
    tid = await create_theme(project_id, theme.name, theme.description)
    return {"id": tid, "name": theme.name}

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
    get_factors_for_theme
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
    return {"id": fid, "name": factor.name}

@app.patch("/factors/{factor_id}")
async def update_factor_route(factor_id: str, factor: FactorUpdate):
    await update_factor_manual(factor_id, factor.name, factor.description, factor.type, factor.theme_id)
    return {"status": "updated"}

@app.delete("/factors/{factor_id}")
async def delete_factor_route(factor_id: str):
    await delete_factor_manual(factor_id)
    return {"status": "deleted"}

@app.post("/claims_manual")
async def create_claim(claim: ClaimManualCreate):
    logger.info(f"Creating claim: {claim}")
    await create_claim_manual(
        claim.theme_id, 
        claim.source_id, 
        claim.target_id, 
        claim.statement, 
        claim.polarity, 
        claim.confidence
    )
    return {"status": "created"}

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
    return {"status": "updated"}

@app.delete("/claims/{claim_id}")
async def delete_claim_route(claim_id: str):
    await delete_claim_manual(claim_id)
    return {"status": "deleted"}
