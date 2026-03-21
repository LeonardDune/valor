from typing import List, Optional, Dict, Any
import uuid
import logging

from app.db.utils import get_driver
from app.models.domain import LifecycleStatus, Proposal

logger = logging.getLogger(__name__)


async def set_conversation_topic(conversation_id: str, topic: str):
    driver = get_driver()
    query = """
    MERGE (c:ConversationThread {id: $cid})
    SET c.topic = $topic, c.updated_at = datetime()
    """
    try:
        with driver.session() as session:
            session.run(query, {"cid": conversation_id, "topic": topic})
    except Exception as e:
        logger.error(f"Failed to set topic: {e}")


async def get_conversation_topic(conversation_id: str) -> Optional[str]:
    driver = get_driver()
    query = "MATCH (c:ConversationThread {id: $cid}) RETURN c.topic as topic"
    try:
        with driver.session() as session:
            result = session.run(query, {"cid": conversation_id})
            record = result.single()
            return record["topic"] if record else None
    except Exception as e:
        return None


# --- Proposals ---

async def create_proposal(title: str, author_id: str, description: Optional[str] = None, type: str = "standard", target_id: Optional[str] = None) -> str:
    driver = get_driver()
    proposal_id = str(uuid.uuid4())

    query = """
    MATCH (u:User {id: $author_id})
    CREATE (p:Proposal {
        id: $id,
        title: $title,
        description: $description,
        type: $type,
        target_id: $target_id,
        status: 'proposed',
        created_at: datetime()
    })
    CREATE (u)-[:CREATED]->(p)
    RETURN p.id as id
    """

    try:
        with driver.session() as session:
            result = session.run(query, {
                "id": proposal_id,
                "title": title,
                "author_id": author_id,
                "description": description,
                "type": type,
                "target_id": target_id
            })
            record = result.single()
            if record:
                return record["id"]
            raise Exception("User not found or creation failed")
    except Exception as e:
        logger.error(f"Error creating proposal: {e}")
        raise e


async def get_proposals(status: Optional[str] = None, author_id: Optional[str] = None) -> List[Proposal]:
    driver = get_driver()

    query = """
    MATCH (p:Proposal)<-[:CREATED]-(u:User)
    """

    where_clauses = []
    params = {}

    if status:
        where_clauses.append("p.status = $status")
        params["status"] = status

    if author_id:
        where_clauses.append("u.id = $author_id")
        params["author_id"] = author_id

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += """
    RETURN p, u.id as author_id
    ORDER BY p.created_at DESC
    """

    try:
        with driver.session() as session:
            result = session.run(query, params)
            proposals = []
            for record in result:
                node = record["p"]
                auth_id = record["author_id"]
                proposals.append(Proposal(
                    id=node["id"],
                    title=node["title"],
                    description=node.get("description"),
                    status=LifecycleStatus(node.get("status", "draft")),
                    author_id=auth_id,
                    type=node.get("type"),
                    target_id=node.get("target_id"),
                    created_at=str(node["created_at"])
                ))
            return proposals
    except Exception as e:
        logger.error(f"Error getting proposals: {e}")
        return []


async def get_proposal_by_id(proposal_id: str) -> Optional[Proposal]:
    driver = get_driver()
    query = """
    MATCH (p:Proposal {id: $id})<-[:CREATED]-(u:User)
    RETURN p, u.id as author_id
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"id": proposal_id})
            record = result.single()
            if record:
                node = record["p"]
                return Proposal(
                    id=node["id"],
                    title=node["title"],
                    description=node.get("description"),
                    status=LifecycleStatus(node.get("status", "draft")),
                    author_id=record["author_id"],
                    type=node.get("type"),
                    target_id=node.get("target_id"),
                    created_at=str(node["created_at"])
                )
            return None
    except Exception as e:
        logger.error(f"Error getting proposal {proposal_id}: {e}")
        return None


async def update_proposal_status(proposal_id: str, status: LifecycleStatus) -> bool:
    driver = get_driver()
    query = """
    MATCH (p:Proposal {id: $id})
    SET p.status = $status
    RETURN p
    """
    try:
        with driver.session() as session:
            status_str = status.value if hasattr(status, 'value') else status
            result = session.run(query, {"id": proposal_id, "status": status_str})
            return result.single() is not None
    except Exception as e:
        logger.error(f"Error updating proposal status: {e}")
        return False


# --- Conversation Threads ---

async def create_conversation_thread(target_id: str, topic: str) -> str:
    driver = get_driver()
    tid = str(uuid.uuid4())
    query = """
    MATCH (s {id: $sid})
    CREATE (t:ConversationThread {id: $id, topic: $topic, status: 'active', created_at: datetime(), target_id: $sid})
    CREATE (s)-[:HAS_THREAD]->(t)
    RETURN t.id as id
    """
    with driver.session() as session:
        return session.run(query, {"sid": target_id, "id": tid, "topic": topic}).single()["id"]


async def get_threads_by_target(target_id: str) -> List[Dict]:
    driver = get_driver()
    query = """
    MATCH (s)
    WHERE s.id = $sid
    MATCH (s)-[:HAS_THREAD]->(t:ConversationThread)
    OPTIONAL MATCH (t)<-[:BELONGS_TO]-(m:ConversationMessage)
    WITH t, s, count(m) as msg_count
    RETURN {
        id: t.id,
        topic: t.topic,
        status: t.status,
        created_at: toString(t.created_at),
        target_id: s.id,
        message_count: msg_count
    } as thread_data
    """
    with driver.session() as session:
        return [r["thread_data"] for r in session.run(query, {"sid": target_id})]


async def get_thread_counts(target_ids: List[str]) -> Dict[str, int]:
    if not target_ids:
        return {}
    driver = get_driver()
    query = """
    MATCH (s)
    WHERE s.id IN $target_ids
    MATCH (s)-[:HAS_THREAD]->(t:ConversationThread)
    RETURN s.id as target_id, count(t) as thread_count
    """
    with driver.session() as session:
        result = session.run(query, {"target_ids": target_ids})
        return {r["target_id"]: r["thread_count"] for r in result}


async def create_thread_message(thread_id: str, user_id: str, content: str) -> Dict[str, Any]:
    driver = get_driver()
    msg_id = str(uuid.uuid4())
    query = """
    MATCH (t:ConversationThread {id: $tid})
    MATCH (u:User {id: $uid})
    CREATE (m:ConversationMessage {id: $mid, content: $content, created_at: datetime(), user_id: $uid})
    CREATE (m)-[:BELONGS_TO]->(t)
    CREATE (u)-[:AUTHORED]->(m)
    RETURN {
        id: m.id,
        content: m.content,
        created_at: toString(m.created_at),
        user_id: m.user_id,
        author_name: coalesce(u.name, u.email)
    } as msg
    """
    with driver.session() as session:
        return session.run(query, {"tid": thread_id, "mid": msg_id, "content": content, "uid": user_id}).single()["msg"]


async def get_thread_messages(thread_id: str) -> List[Dict[str, Any]]:
    driver = get_driver()
    query = """
    MATCH (m:ConversationMessage)-[:BELONGS_TO]->(t:ConversationThread {id: $tid})
    OPTIONAL MATCH (u:User)-[:AUTHORED]->(m)
    RETURN {
        id: m.id,
        content: m.content,
        created_at: toString(m.created_at),
        user_id: m.user_id,
        author_name: coalesce(u.name, u.email, 'Unknown')
    } as msg
    ORDER BY m.created_at ASC
    """
    with driver.session() as session:
        return [r["msg"] for r in session.run(query, {"tid": thread_id})]
