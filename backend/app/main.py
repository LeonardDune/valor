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

from app.db.crud import create_project, get_projects, create_theme, get_project_themes
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
