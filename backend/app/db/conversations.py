from typing import List, Optional, Dict, Any
import uuid
import logging

from app.db.utils import get_driver
from app.models.domain import LifecycleStatus, Claim, Proposal

logger = logging.getLogger(__name__)


# --- Agent / Conversation ---

async def save_claims(conversation_id: str, claims: List[Claim]):
    """
    Persists claims extracted by the Agent.
    Updated for Base/Version Refactor:
    - Creates FactorBase/FactorVersion if not exist.
    - Creates ClaimBase/ClaimVersion.
    - Uses active ThemeVersion.
    """
    driver = get_driver()
    query = """
    MERGE (ct:ConversationThread {id: $cid})
    WITH ct, ct.space_id as version_id

    // Ensure we have an active ThemeVersion to attach to
    MATCH (v:ThemeVersion {id: version_id})
    WHERE v.status = 'active'

    UNWIND $claims as claim

    // --- Source Factor ---
    // Try to find existing active FactorVersion by name within this ThemeVersion
    OPTIONAL MATCH (v)-[:HAS_FACTOR]->(existing_fv_source:FactorVersion {name: claim.source_node})
    WITH ct, v, claim, existing_fv_source

    CALL {
        WITH v, claim, existing_fv_source
        // IF existing found, use it. ELSE create new Base + Version
        WHERE existing_fv_source IS NULL
        CREATE (fb_source:FactorBase {
            id: randomUUID(),
            created_at: datetime(),
            created_by: 'system_agent' // Agent doesn't have ID yet?
        })
        CREATE (fv_source:FactorVersion {
            id: randomUUID(),
            base_id: fb_source.id,
            name: claim.source_node,
            // type removed - now context-dependent on relationship
            version_id: v.id,
            created_at: datetime()
        })
        CREATE (v)-[:HAS_FACTOR {role: coalesce(claim.source_type, 'systeemelement')}]->(fv_source)
        // No User-Created ink for agent? Or link to System Admin?
        RETURN fv_source as source_v

        UNION

        WITH existing_fv_source
        WHERE existing_fv_source IS NOT NULL
        RETURN existing_fv_source as source_v
    }

    // --- Target Factor (Same logic) ---
    WITH ct, v, claim, source_v
    OPTIONAL MATCH (v)-[:HAS_FACTOR]->(existing_fv_target:FactorVersion {name: claim.target_node})

    CALL {
        WITH v, claim, existing_fv_target
        WHERE existing_fv_target IS NULL
        CREATE (fb_target:FactorBase {
            id: randomUUID(),
            created_at: datetime(),
            created_by: 'system_agent'
        })
        CREATE (fv_target:FactorVersion {
            id: randomUUID(),
            base_id: fb_target.id,
            name: claim.target_node,
            // type removed - now context-dependent on relationship
            version_id: v.id,
            created_at: datetime()
        })
        CREATE (v)-[:HAS_FACTOR {role: coalesce(claim.target_type, 'systeemelement')}]->(fv_target)
        RETURN fv_target as target_v

        UNION

        WITH existing_fv_target
        WHERE existing_fv_target IS NOT NULL
        RETURN existing_fv_target as target_v
    }

    // --- Claim ---
    CREATE (cb:ClaimBase {
        id: coalesce(claim.id, randomUUID()),
        created_at: datetime(),
        created_by: 'system_agent'
    })
    CREATE (cv:ClaimVersion {
        id: randomUUID(),
        base_id: cb.id,
        statement: claim.statement,
        confidence: claim.confidence,
        polarity: claim.polarity,
        evidence_text: claim.evidence_text,
        evidence_url: claim.evidence_url,
        source_version_id: source_v.id,
        target_version_id: target_v.id,
        created_at: datetime()
    })

    // Link ClaimVersion to FactorVersions
    CREATE (source_v)-[:CLAIMS]->(cv)
    CREATE (cv)-[:TO]->(target_v)

    // Link to Conversation
    MERGE (ct)-[:GENERATED]->(cv)
    """

    # Note: Logic above is simplified "Merge if not exists" using CALL/UNION
    # Agent logic is complex. For now focusing on manual endpoints.
    # Placeholder for Agent logic update until verified.
    pass


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


async def fetch_existing_factors(conversation_id: str) -> List[str]:
    """Returns names of factors mentioned in this conversation or context."""
    driver = get_driver()
    query = """
    MATCH (c:ConversationThread {id: $cid})-[:GENERATED]->(cl:ClaimVersion)
    MATCH (source)-[:CLAIMS]->(cl)-[:TO]->(target)
    RETURN collect(distinct source.name) + collect(distinct target.name) as factors
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"cid": conversation_id})
            record = result.single()
            if record:
                names = list(set(record["factors"]))
                return names
            return []
    except Exception as e:
        logger.error(f"Failed to fetch factors: {e}")
        return []


async def revoke_claims(conversation_id: str):
    """Marks claims from this conversation as revoked or deletes them?"""
    driver = get_driver()
    query = """
    MATCH (c:ConversationThread {id: $cid})-[rel:GENERATED]->(cl:ClaimVersion)
    DETACH DELETE cl
    """
    try:
        with driver.session() as session:
            session.run(query, {"cid": conversation_id})
    except Exception as e:
        logger.error(f"Failed to revoke claims: {e}")


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
