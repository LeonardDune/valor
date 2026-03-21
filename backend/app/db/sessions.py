from typing import List, Optional, Dict, Any, Tuple
import uuid
import logging
import json
from app.db.utils import get_driver
from app.models.domain import VotingSession

logger = logging.getLogger(__name__)


async def create_voting_session(ds_id: str, created_by: str, config: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """Maakt een nieuwe votingsessie aan, verankerd op DesignSpace. Retourneert (session_id, project_id)."""
    driver = get_driver()
    session_id = str(uuid.uuid4())
    config_json = json.dumps(config)

    close_query = """
    MATCH (ds:DesignSpace {id: $dsId})-[:HAS_SESSION]->(s:VotingSession)
    WHERE s.status = 'active'
    SET s.status = 'closed', s.ended_at = datetime()
    """

    create_query = """
    MATCH (ds:DesignSpace {id: $dsId})
    OPTIONAL MATCH (p:Project)-[:hasIssue]->(:Issue)-[:isAddressedInDesignSpace]->(ds)
    CREATE (s:VotingSession {
        id: $sid,
        status: 'active',
        stage: 'refine',
        config: $config,
        created_at: datetime(),
        created_by: $uid
    })
    CREATE (ds)-[:HAS_SESSION]->(s)
    RETURN s.id AS id, p.id AS project_id
    """

    try:
        with driver.session() as session:
            session.run(close_query, {"dsId": ds_id})
            result = session.run(create_query, {
                "dsId": ds_id,
                "sid": session_id,
                "config": config_json,
                "uid": created_by,
            })
            record = result.single()
            if record:
                return record["id"], record["project_id"]
            raise Exception("Aanmaken sessie mislukt (DesignSpace niet gevonden?)")
    except Exception as e:
        logger.error(f"Error creating voting session: {e}")
        raise e


async def update_voting_session(session_id: str, status: str) -> Optional[str]:
    """Werkt sessiestatus bij, retourneert project_id voor broadcasting."""
    driver = get_driver()
    query = """
    MATCH (s:VotingSession {id: $sid})
    OPTIONAL MATCH (ds:DesignSpace)-[:HAS_SESSION]->(s)
    OPTIONAL MATCH (p:Project)-[:hasIssue]->(:Issue)-[:isAddressedInDesignSpace]->(ds)
    SET s.status = $status
    RETURN p.id AS project_id
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"sid": session_id, "status": status})
            record = result.single()
            return record["project_id"] if record else None
    except Exception as e:
        logger.error(f"Error updating voting session: {e}")
        return None


async def get_active_session(ds_id: str) -> Optional[VotingSession]:
    driver = get_driver()
    query = """
    MATCH (ds:DesignSpace {id: $dsId})-[:HAS_SESSION]->(s:VotingSession)
    WHERE s.status = 'active'
    RETURN s, ds.id AS ds_id
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"dsId": ds_id})
            record = result.single()
            if record:
                node = record["s"]
                config_str = node.get("config", "{}")
                try:
                    config = json.loads(config_str)
                except Exception:
                    config = {}
                return VotingSession(
                    id=node["id"],
                    theme_version_id=record["ds_id"],
                    status=node.get("status", "active"),
                    stage=node.get("stage", "refine"),
                    config=config,
                    created_by=node.get("created_by", "system"),
                    created_at=str(node.get("created_at")),
                )
            return None
    except Exception as e:
        logger.error(f"Error getting active session: {e}")
        return None


async def get_context_ids(ds_id: str) -> Tuple[Optional[str], Optional[str]]:
    """Retourneert (issue_id, project_id) voor een DesignSpace."""
    driver = get_driver()
    query = """
    MATCH (ds:DesignSpace {id: $dsId})
    OPTIONAL MATCH (i:Issue)-[:isAddressedInDesignSpace]->(ds)
    OPTIONAL MATCH (p:Project)-[:hasIssue]->(i)
    RETURN i.id AS issue_id, p.id AS project_id
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"dsId": ds_id})
            record = result.single()
            if record:
                return record["issue_id"], record["project_id"]
            return None, None
    except Exception as e:
        logger.error(f"Error getting context ids: {e}")
        return None, None


async def get_session_context(session_id: str) -> Tuple[Optional[str], Optional[str]]:
    """Traverseert session → DesignSpace → Issue → Project. Retourneert (issue_id, project_id)."""
    driver = get_driver()
    query = """
    MATCH (s:VotingSession {id: $sid})
    OPTIONAL MATCH (ds:DesignSpace)-[:HAS_SESSION]->(s)
    OPTIONAL MATCH (i:Issue)-[:isAddressedInDesignSpace]->(ds)
    OPTIONAL MATCH (p:Project)-[:hasIssue]->(i)
    RETURN i.id AS issue_id, p.id AS project_id
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"sid": session_id})
            record = result.single()
            if record:
                return record["issue_id"], record["project_id"]
            return None, None
    except Exception as e:
        logger.error(f"Error getting session context: {e}")
        return None, None


async def get_moderator_sessions(user_id: str) -> List[Dict[str, Any]]:
    """Retourneert alle actieve votingsessies waar de gebruiker moderator of admin is."""
    driver = get_driver()
    query = """
    MATCH (u:User {id: $uid})-[r:HAS_ROLE]->(ds:DesignSpace)
    WHERE r.role IN ['moderator', 'admin']
    MATCH (ds)-[:HAS_SESSION]->(s:VotingSession)
    WHERE s.status = 'active'
    OPTIONAL MATCH (i:Issue)-[:isAddressedInDesignSpace]->(ds)
    RETURN DISTINCT s.id AS id,
                    s.stage AS stage,
                    s.created_at AS created_at,
                    i.name AS issue_name,
                    ds.id AS ds_id
    ORDER BY s.created_at DESC
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"uid": user_id})
            return [dict(record) for record in result]
    except Exception as e:
        logger.error(f"Error getting moderator sessions: {e}")
        return []
