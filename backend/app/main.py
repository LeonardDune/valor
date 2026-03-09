from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
import uuid
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from app.models.domain import ConversationRequest, ConversationResponse
from app.db.utils import close_driver, verify_connectivity
from app.agent.core import process_user_message
from app.db.crud import set_conversation_topic
from app.services.connection_manager import manager
from app.routers import proposals, dashboard, threads, sessions, deliberation
from app.routers import factors, claims, organizations, hierarchy

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    await verify_connectivity()
    await startup_migration()
    yield
    logger.info("Shutting down...")
    close_driver()


async def startup_migration():
    """Ensures a default organization and user exist, and links orphaned projects."""
    try:
        from app.db.crud import (
            create_organization, get_organizations, get_driver,
        )

        orgs = await get_organizations()
        default_org_id = None
        if not orgs:
            logger.info("No organizations found. Creating Default Organization.")
            default_org_id = await create_organization("Default Organization", "Auto-created during migration")
        else:
            default_org_id = orgs[0]['id']

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


app = FastAPI(title="CAUSA Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://valor-ecosystem.nl",
        "https://api.valor-ecosystem.nl",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(proposals.router)
app.include_router(dashboard.router)
app.include_router(threads.router)
app.include_router(sessions.router)
app.include_router(deliberation.router)
app.include_router(organizations.router)
app.include_router(hierarchy.router)
app.include_router(factors.router)
app.include_router(claims.router)


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

    response = await process_user_message(request.message, cid)

    # Agent writes disabled (Production Safety)
    return response


@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str, token: Optional[str] = None):
    user_id = f"anon-{uuid.uuid4().hex[:6]}"

    if token:
        try:
            from app.auth import verify_token_string
            payload = verify_token_string(token)
            user_id = payload.get("email") or payload.get("sub") or user_id
            logger.info(f"WebSocket Authenticated: {user_id} for Project {project_id}")
        except Exception as e:
            logger.error(f"WebSocket Auth Failed for project {project_id}. Error: {e}")
    else:
        logger.warning(f"WebSocket connection without Token for {project_id}")

    await manager.connect(websocket, project_id, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            if isinstance(data, dict):
                if "payload" not in data:
                    data["payload"] = {}
                if "user_id" in data["payload"]:
                    data["payload"]["user_id"] = user_id
                if data.get("type") == "NODE_FOCUS":
                    data["payload"]["user_id"] = user_id
            await manager.broadcast_presence(project_id, user_id, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, project_id, user_id)
