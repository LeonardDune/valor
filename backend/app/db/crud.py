import logging
from typing import List, Optional
from app.db.utils import get_driver
from app.models.domain import Claim, ChatMessage

logger = logging.getLogger(__name__)

async def save_claims(conversation_id: str, claims: List[Claim]):
    if not claims:
        return
    
    driver = get_driver()
    query = """
    UNWIND $claims AS claim
    MERGE (source:Factor {name: claim.source_node})
    ON CREATE SET source.id = randomUUID()
    MERGE (target:Factor {name: claim.target_node})
    ON CREATE SET target.id = randomUUID()
    
    MERGE (c:Claim {id: claim.id})
    SET c.statement = claim.statement,
        c.confidence = claim.confidence,
        c.polarity = claim.polarity,
        c.relationship_type = claim.relationship_type,
        c.created_at = datetime(claim.created_at)
        
    MERGE (source)-[:CLAIMS]-(c)
    MERGE (c)-[:TO]->(target)
    
    WITH c, claim
    MATCH (t:ConversationThread {id: $conversation_id})
    MERGE (t)-[:GENERATED]->(c)
    """
    
    # Prepare data for Neo4j (dict serialization)
    claims_data = [c.model_dump(mode='json') for c in claims]
    
    try:
        with driver.session() as session:
            # Ensure conversation exists first (simple check)
            session.run("""
                MERGE (t:ConversationThread {id: $cid})
                ON CREATE SET t.created_at = datetime()
            """, {"cid": conversation_id})
            
            session.run(query, {"claims": claims_data, "conversation_id": conversation_id})
            logger.info(f"Persisted {len(claims)} claims for conversation {conversation_id}")
    except Exception as e:
        logger.error(f"Failed to save claims: {e}")
        raise e

async def revoke_claims(conversation_id: str, revocations: List[dict]):
    if not revocations:
        return

    driver = get_driver()
    query = """
    UNWIND $revocations AS rev
    MATCH (t:ConversationThread {id: $cid})
    MATCH (s:Factor {name: rev.source})-[:CLAIMS]-(c:Claim)-[:TO]->(target:Factor {name: rev.target})
    MATCH (t)-[:GENERATED]->(c)
    DETACH DELETE c
    """
    try:
        with driver.session() as session:
            session.run(query, {"cid": conversation_id, "revocations": revocations})
            logger.info(f"Revoked {len(revocations)} claims for conversation {conversation_id}")
    except Exception as e:
        logger.error(f"Failed to revoke claims: {e}")


async def get_claims_for_conversation(conversation_id: str) -> List[Claim]:
    driver = get_driver()
    query = """
    MATCH (t:ConversationThread {id: $cid})-[:GENERATED]->(c:Claim)
    MATCH (s:Factor)-[:CLAIMS]-(c)-[:TO]->(t_node:Factor)
    RETURN c, s.name as source, t_node.name as target
    """
    
    try:
        with driver.session() as session:
            result = session.run(query, {"cid": conversation_id})
            claims = []
            for record in result:
                node = record["c"]
                # Reconstruct Claim object
                # Note: node properties are Dict
                claim_data = dict(node)
                claim_data['source_node'] = record["source"]
                claim_data['target_node'] = record["target"]
                claims.append(Claim(**claim_data))
            return claims
    except Exception as e:
        logger.error(f"Failed to fetch claims: {e}")
        return []

async def fetch_existing_factors(conversation_id: str) -> List[str]:
    driver = get_driver()
    # Find all factors within the SAME THEME scope.
    # If no theme, fall back to just the thread.
    query = """
    MATCH (t:ConversationThread {id: $cid})
    OPTIONAL MATCH (t)-[:BELONGS_TO]->(th:Theme)<-[:BELONGS_TO]-(other_t:ConversationThread)
    WITH coalesce(other_t, t) as scope_thread
    MATCH (scope_thread)-[:GENERATED]->(c:Claim)
    MATCH (c)-[:TO|CLAIMS]-(f:Factor)
    RETURN DISTINCT f.name as name
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"cid": conversation_id})
            return [record["name"] for record in result]
    except Exception as e:
        logger.error(f"Failed to fetch factors: {e}")
        return []

async def set_conversation_topic(conversation_id: str, topic: str):
    driver = get_driver()
    query = """
    MERGE (t:ConversationThread {id: $cid})
    ON CREATE SET t.created_at = datetime()
    
    MERGE (th:Theme {name: $topic})
    MERGE (t)-[:BELONGS_TO]->(th)
    """
    try:
        with driver.session() as session:
            session.run(query, {"cid": conversation_id, "topic": topic})
    except Exception as e:
        logger.error(f"Failed to set topic: {e}")

async def get_conversation_topic(conversation_id: str) -> Optional[str]:
    driver = get_driver()
    query = """
    MATCH (t:ConversationThread {id: $cid})-[:BELONGS_TO]->(th:Theme)
    RETURN th.name as topic
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"cid": conversation_id})
            record = result.single()
            if record:
                return record["topic"]
            return None
    except Exception as e:
        logger.error(f"Failed to get topic: {e}")
        return None
