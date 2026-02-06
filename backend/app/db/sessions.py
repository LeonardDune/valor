from typing import Optional, Dict, Any, Tuple
import uuid
import logging
import json
from datetime import datetime
from app.db.utils import get_driver
from app.models.domain import VotingSession

logger = logging.getLogger(__name__)

async def create_voting_session(theme_version_id: str, created_by: str, config: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """
    Creates a new voting session and returns (session_id, project_id).
    project_id is needed for broadcasting.
    """
    driver = get_driver()
    session_id = str(uuid.uuid4())
    
    # Serialize config to string for Neo4j property storage
    config_json = json.dumps(config)
    
    # 1. Close any existing active sessions
    close_query = """
    MATCH (v:ThemeVersion {id: $vid})-[:HAS_SESSION]->(s:VotingSession)
    WHERE s.status = 'active'
    SET s.status = 'closed', s.ended_at = datetime()
    """
    
    # 2. Create new session and fetch Project ID context
    create_query = """
    MATCH (v:ThemeVersion {id: $vid})
    OPTIONAL MATCH (v)<-[:HAS_VERSION]-(t:Theme)<-[:HAS_THEME]-(p:Project)
    CREATE (s:VotingSession {
        id: $sid,
        status: 'active',
        config: $config,
        created_at: datetime(),
        created_by: $uid
    })
    CREATE (v)-[:HAS_SESSION]->(s)
    RETURN s.id as id, p.id as project_id
    """

    try:
        with driver.session() as session:
            session.run(close_query, {"vid": theme_version_id})
            result = session.run(create_query, {
                "vid": theme_version_id, 
                "sid": session_id, 
                "config": config_json, 
                "uid": created_by
            })
            record = result.single()
            if record:
                return record["id"], record["project_id"]
            raise Exception("Failed to create session (ThemeVersion not found?)")
    except Exception as e:
        logger.error(f"Error creating voting session: {e}")
        raise e

async def update_voting_session(session_id: str, status: str) -> Optional[str]:
    """
    Updates session status and returns project_id for broadcasting.
    """
    driver = get_driver()
    query = """
    MATCH (s:VotingSession {id: $sid})
    OPTIONAL MATCH (s)<-[:HAS_SESSION]-(v:ThemeVersion)<-[:HAS_VERSION]-(t:Theme)<-[:HAS_THEME]-(p:Project)
    SET s.status = $status
    RETURN s.id, p.id as project_id
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"sid": session_id, "status": status})
            record = result.single()
            if record:
                return record["project_id"]
            return None
    except Exception as e:
        logger.error(f"Error updating voting session: {e}")
        return None

async def get_active_session(theme_version_id: str) -> Optional[VotingSession]:
    driver = get_driver()
    query = """
    MATCH (v:ThemeVersion {id: $vid})-[:HAS_SESSION]->(s:VotingSession)
    WHERE s.status = 'active'
    RETURN s, v.id as vid
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"vid": theme_version_id})
            record = result.single()
            if record:
                node = record["s"]
                config_str = node.get("config", "{}")
                try:
                    config = json.loads(config_str)
                except:
                    config = {}
                    
                return VotingSession(
                    id=node["id"],
                    theme_version_id=record["vid"],
                    status=node.get("status", "active"),
                    config=config,
                    created_by=node.get("created_by", "system"),
                    created_at=str(node.get("created_at")) 
                )
            return None
    except Exception as e:
        logger.error(f"Error getting active session: {e}")
        return None

async def get_context_ids(version_id: str) -> Tuple[Optional[str], Optional[str]]:
    driver = get_driver()
    query = """
    MATCH (v:ThemeVersion {id: $vid})
    OPTIONAL MATCH (v)<-[:HAS_VERSION]-(t:Theme)
    OPTIONAL MATCH (t)<-[:HAS_THEME]-(p:Project)
    RETURN t.id as theme_id, p.id as project_id
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"vid": version_id})
            record = result.single()
            if record:
                return record["theme_id"], record["project_id"]
            return None, None
    except Exception as e:
        logger.error(f"Error getting context ids: {e}")
        return None, None

async def get_session_context(session_id: str) -> Tuple[Optional[str], Optional[str]]:
    driver = get_driver()
    query = """
    MATCH (s:VotingSession {id: $sid})
    OPTIONAL MATCH (s)<-[:HAS_SESSION]-(v:ThemeVersion)<-[:HAS_VERSION]-(t:Theme)
    OPTIONAL MATCH (t)<-[:HAS_THEME]-(p:Project)
    RETURN t.id as theme_id, p.id as project_id
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"sid": session_id})
            record = result.single()
            if record:
                return record["theme_id"], record["project_id"]
            return None, None
    except Exception as e:
        logger.error(f"Error getting session context: {e}")
        return None, None
