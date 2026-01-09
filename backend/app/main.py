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
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up...")
    await verify_connectivity()
    yield
    # Shutdown
    logger.info("Shutting down...")
    close_driver()

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
    create_project, get_projects, create_theme, get_project_themes,
    get_claims_for_theme
)
from pydantic import BaseModel

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ThemeCreate(BaseModel):
    project_id: str
    name: str
    description: Optional[str] = None

@app.get("/projects")
async def list_projects():
    return await get_projects()

@app.post("/projects")
async def create_new_project(project: ProjectCreate):
    pid = await create_project(project.name, project.description)
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
    await update_factor_manual(factor_id, factor.name, factor.description, factor.type)
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
