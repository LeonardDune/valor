import logging
import uuid
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
    SET source.id = coalesce(source.id, randomUUID())
    
    MERGE (target:Factor {name: claim.target_node})
    ON CREATE SET target.id = randomUUID()
    SET target.id = coalesce(target.id, randomUUID())
    
    MERGE (c:Claim {id: claim.id})
    SET c.statement = claim.statement,
        c.confidence = claim.confidence,
        c.polarity = claim.polarity,
        c.relationship_type = claim.relationship_type,
        c.created_at = datetime(claim.created_at)
        
    MERGE (source)-[:CLAIMS]-(c)
    MERGE (c)-[:TO]->(target)
    
    WITH c, claim, source, target
    MATCH (t:ConversationThread {id: $conversation_id})
    MERGE (t)-[:GENERATED]->(c)
    
    WITH source, target, t, claim
    OPTIONAL MATCH (t)-[:BELONGS_TO]->(th:Theme)
    FOREACH (_ IN CASE WHEN th IS NOT NULL THEN [1] ELSE [] END |
        MERGE (th)-[r1:HAS_FACTOR]->(source)
        SET r1.role = coalesce(claim.source_type, r1.role, 'systeemelement')
        MERGE (th)-[r2:HAS_FACTOR]->(target)
        SET r2.role = coalesce(claim.target_type, r2.role, 'systeemelement')
    )
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
    RETURN c, s.name as source, s.id as source_id, t_node.name as target, t_node.id as target_id
    """
    
    try:
        with driver.session() as session:
            result = session.run(query, {"cid": conversation_id})
            claims = []
            for record in result:
                node = record["c"]
                claim_data = dict(node)
                claim_data['source_node'] = record["source"]
                claim_data['source_id'] = record["source_id"]
                claim_data['target_node'] = record["target"]
                claim_data['target_id'] = record["target_id"]
                claims.append(Claim(**claim_data))
            return claims
    except Exception as e:
        logger.error(f"Failed to fetch claims: {e}")
        return []

async def get_claims_for_theme(theme_id: str) -> List[Claim]:
    driver = get_driver()
    # Fetch claims across all threads in this theme
    query = """
    MATCH (th:Theme {id: $tid})<-[:BELONGS_TO]-(t:ConversationThread)-[:GENERATED]->(c:Claim)
    MATCH (s:Factor)-[:CLAIMS]-(c)-[:TO]->(t_node:Factor)
    OPTIONAL MATCH (th)-[rs:HAS_FACTOR]->(s)
    OPTIONAL MATCH (th)-[rt:HAS_FACTOR]->(t_node)
    RETURN c, s.name as source, s.id as source_id, rs.role as s_type, 
           t_node.name as target, t_node.id as target_id, rt.role as t_type
    """
    
    try:
        with driver.session() as session:
            result = session.run(query, {"tid": theme_id})
            claims = []
            for record in result:
                node = record["c"]
                claim_data = dict(node)
                claim_data['source_node'] = record["source"]
                claim_data['source_id'] = record["source_id"]
                claim_data['source_type'] = record["s_type"]
                claim_data['target_node'] = record["target"]
                claim_data['target_id'] = record["target_id"]
                claim_data['target_type'] = record["t_type"]
                # Convert neo4j datetime to string for Pydantic if necessary
                if 'created_at' in claim_data and hasattr(claim_data['created_at'], 'isoformat'):
                    claim_data['created_at'] = claim_data['created_at'].isoformat()
                claims.append(Claim(**claim_data))
            return claims
    except Exception as e:
        logger.error(f"Failed to fetch theme claims: {e}")
        return []

async def get_factors_for_theme(theme_id: str) -> List[dict]:
    driver = get_driver()
    query = """
    MATCH (th:Theme {id: $tid})-[r:HAS_FACTOR]->(f:Factor)
    RETURN f.id as id, f.name as name, f.description as description, r.role as type
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"tid": theme_id})
            return [dict(record) for record in result]
    except Exception as e:
        logger.error(f"Failed to fetch theme factors: {e}")
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
    RETURN DISTINCT f.name as name, f.type as type
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"cid": conversation_id})
            return [f"{record['name']} ({record['type']})" for record in result]
    except Exception as e:
        logger.error(f"Failed to fetch factors: {e}")
        return []

async def set_conversation_topic(conversation_id: str, topic: str):
    driver = get_driver()
    query = """
    MERGE (t:ConversationThread {id: $cid})
    ON CREATE SET t.created_at = datetime()
    
    MERGE (th:Theme {name: $topic})
    ON CREATE SET th.id = randomUUID(), th.created_at = datetime()
    SET th.id = coalesce(th.id, randomUUID())
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

# Project & Theme Hierarchy Management

async def create_project(name: str, description: Optional[str] = None) -> str:
    driver = get_driver()
    pid = str(uuid.uuid4())
    query = """
    MERGE (p:Project {id: $pid})
    ON CREATE SET p.name = $name, 
                  p.description = $desc,
                  p.created_at = datetime()
    RETURN p.id as id
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"pid": pid, "name": name, "desc": description})
            return result.single()["id"]
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise e

async def get_projects():
    driver = get_driver()
    query = """
    MATCH (p:Project)
    RETURN p.id as id, p.name as name, p.description as description, p.created_at as created_at
    ORDER BY p.created_at DESC
    """
    try:
        with driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]
    except Exception as e:
        logger.error(f"Failed to get projects: {e}")
        return []

async def create_theme(project_id: str, name: str, description: Optional[str] = None) -> str:
    driver = get_driver()
    tid = str(uuid.uuid4())
    query = """
    MATCH (p:Project {id: $pid})
    MERGE (t:Theme {name: $name})
    ON CREATE SET t.id = $tid, 
                  t.description = $desc,
                  t.created_at = datetime()
    ON MATCH SET t.id = coalesce(t.id, $tid, randomUUID()),
                 t.description = coalesce($desc, t.description)
    MERGE (p)-[:HAS_THEME]->(t)
    RETURN t.id as id
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"pid": project_id, "name": name, "desc": description, "tid": tid})
            record = result.single()
            return record["id"] if record else None
    except Exception as e:
        logger.error(f"Failed to create theme: {e}")
        raise e

async def get_project_themes(project_id: str):
    driver = get_driver()
    query = """
    MATCH (p:Project {id: $pid})-[:HAS_THEME]->(t:Theme)
    RETURN t.id as id, t.name as name, t.description as description
    ORDER BY t.created_at DESC
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"pid": project_id})
            return [dict(record) for record in result]
    except Exception as e:
        logger.error(f"Failed to get themes: {e}")
        return []

# Manual Factor & Claim Management

async def create_factor_manual(name: str, description: Optional[str] = None, type: str = "systeemelement", theme_id: Optional[str] = None) -> str:
    driver = get_driver()
    fid = str(uuid.uuid4())
    query = """
    MERGE (f:Factor {name: $name})
    ON CREATE SET f.id = $fid, 
                  f.description = $desc,
                  f.type = $type
    ON MATCH SET f.id = coalesce(f.id, $fid, randomUUID()),
                 f.description = coalesce($desc, f.description)
    WITH f
    OPTIONAL MATCH (th:Theme {id: $tid})
    FOREACH (ignored in CASE WHEN th IS NOT NULL THEN [1] ELSE [] END |
        MERGE (th)-[r:HAS_FACTOR]->(f)
        SET r.role = $type
    )
    RETURN f.id as id
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"name": name, "desc": description, "fid": fid, "type": type, "tid": theme_id})
            record = result.single()
            return record["id"] if record else None
    except Exception as e:
        logger.error(f"Failed to create factor manually: {e}")
        raise e

async def update_factor_manual(factor_id: str, name: Optional[str] = None, description: Optional[str] = None, type: Optional[str] = None, theme_id: Optional[str] = None):
    driver = get_driver()
    # Update Node properties
    query_node = """
    MATCH (f:Factor) WHERE f.id = $fid OR f.name = $fid
    SET f.name = coalesce($name, f.name),
        f.description = coalesce($desc, f.description)
    """
    
    # Update Relationship Role (if theme_id is provided)
    query_rel = """
    MATCH (f:Factor) WHERE f.id = $fid OR f.name = $fid
    MATCH (th:Theme {id: $tid})-[r:HAS_FACTOR]-(f)
    SET r.role = coalesce($type, r.role)
    """
    
    try:
        with driver.session() as session:
            session.run(query_node, {"fid": factor_id, "name": name, "desc": description})
            if theme_id and type:
                 session.run(query_rel, {"fid": factor_id, "tid": theme_id, "type": type})
    except Exception as e:
        logger.error(f"Failed to update factor: {e}")
        raise e

async def create_claim_manual(theme_id: str, source_id: str, target_id: str, statement: str, polarity: str = "+", confidence: float = 1.0):
    driver = get_driver()
    cid = str(uuid.uuid4())
    # Match by ID or Name as fallback
    query = """
    MATCH (th:Theme {id: $theme_id})
    
    // Find Source (by ID or Name)
    OPTIONAL MATCH (s:Factor) WHERE s.id = $sid OR s.name = $sid
    
    // Find Target (by ID or Name)
    OPTIONAL MATCH (t:Factor) WHERE t.id = $tid OR t.name = $tid
    
    WITH th, s, t
    WHERE s IS NOT NULL AND t IS NOT NULL
    
    // Create or find a manual edits thread for this theme
    MERGE (thread:ConversationThread {id: "manual_" + $theme_id})
    ON CREATE SET thread.created_at = datetime(), thread.name = "Manual Edits"
    MERGE (thread)-[:BELONGS_TO]->(th)
    
    MERGE (c:Claim {id: $cid})
    SET c.statement = $statement,
        c.polarity = $polarity,
        c.confidence = $confidence,
        c.relationship_type = 'CAUSES',
        c.created_at = datetime()
        
    MERGE (s)-[:CLAIMS]-(c)
    MERGE (c)-[:TO]->(t)
    MERGE (thread)-[:GENERATED]->(c)
    
    // Ensure factors are linked to the theme
    MERGE (th)-[r1:HAS_FACTOR]->(s)
    SET r1.role = coalesce(r1.role, 'systeemelement')
    MERGE (th)-[r2:HAS_FACTOR]->(t)
    SET r2.role = coalesce(r2.role, 'systeemelement')
    RETURN c.id as id
    """
    try:
        with driver.session() as session:
            result = session.run(query, {
                "sid": source_id, 
                "tid": target_id, 
                "theme_id": theme_id,
                "statement": statement,
                "polarity": polarity,
                "confidence": confidence,
                "cid": cid
            })
            record = result.single()
            if not record:
                logger.warning(f"Failed to create manual claim: Theme, Source or Target not found. theme_id={theme_id}, sid={source_id}, tid={target_id}")
                return None
            return record["id"]
    except Exception as e:
        logger.error(f"Failed to create claim manually: {e}")
        raise e

async def update_claim_manual(claim_id: str, statement: Optional[str] = None, polarity: Optional[str] = None, confidence: Optional[float] = None, source_id: Optional[str] = None, target_id: Optional[str] = None):
    driver = get_driver()
    query = """
    MATCH (c:Claim {id: $cid})
    SET c.statement = coalesce($statement, c.statement),
        c.polarity = coalesce($polarity, c.polarity),
        c.confidence = coalesce($confidence, c.confidence)
    
    WITH c
    CALL {
        WITH c
        WITH c WHERE $sid IS NOT NULL
        MATCH (s_new:Factor {id: $sid})
        OPTIONAL MATCH (s_old:Factor)-[r1:CLAIMS]-(c)
        DELETE r1
        MERGE (s_new)-[:CLAIMS]-(c)
    }
    CALL {
        WITH c
        WITH c WHERE $tid IS NOT NULL
        MATCH (t_new:Factor {id: $tid})
        OPTIONAL MATCH (c)-[r2:TO]->(t_old:Factor)
        DELETE r2
        MERGE (c)-[:TO]->(t_new)
    }
    """
    try:
        with driver.session() as session:
            session.run(query, {
                "cid": claim_id, 
                "statement": statement, 
                "polarity": polarity, 
                "confidence": confidence,
                "sid": source_id,
                "tid": target_id
            })
    except Exception as e:
        logger.error(f"Failed to update claim: {e}")
        raise e

async def delete_factor_manual(factor_id: str):
    driver = get_driver()
    # Detach delete factor and also any claims that ONLY belonged to this factor
    query = """
    MATCH (f:Factor) WHERE f.id = $fid OR f.name = $fid
    OPTIONAL MATCH (f)-[:CLAIMS|TO]-(c:Claim)
    DETACH DELETE f, c
    """
    try:
        with driver.session() as session:
            session.run(query, {"fid": factor_id})
    except Exception as e:
        logger.error(f"Failed to delete factor: {e}")
        raise e

async def delete_claim_manual(claim_id: str):
    driver = get_driver()
    query = """
    MATCH (c:Claim {id: $cid})
    DETACH DELETE c
    """
    try:
        with driver.session() as session:
            session.run(query, {"cid": claim_id})
    except Exception as e:
        logger.error(f"Failed to delete claim: {e}")
        raise e
