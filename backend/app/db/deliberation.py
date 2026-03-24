from typing import List, Optional, Dict, Any, Tuple
import uuid
import logging
from datetime import datetime
from app.db.utils import get_driver
from app.models.domain import Feedback, Ranking, RankingCategory

logger = logging.getLogger(__name__)

async def submit_feedback(feedback: Feedback) -> bool:
    driver = get_driver()
    query = """
    MATCH (s:VotingSession {id: $sid})
    MATCH (u:User {id: $uid})

    // Delete existing feedback from this user for this tessera in this session
    OPTIONAL MATCH (u)-[old:GAVE_FEEDBACK]->(f_old:Feedback)
    WHERE f_old.session_id = $sid AND f_old.tessera_base_id = $tbid
    DETACH DELETE f_old

    MERGE (f:Feedback {id: $fid})
    ON CREATE SET
        f.session_id = $sid,
        f.tessera_base_id = $tbid,
        f.color = $color,
        f.motivation = $motivation,
        f.created_at = datetime($now)
    ON MATCH SET
        f.color = $color,
        f.motivation = $motivation,
        f.updated_at = datetime($now)

    MERGE (u)-[:GAVE_FEEDBACK]->(f)
    MERGE (s)-[:COLLECTED]->(f)
    RETURN f.id
    """
    try:
        with driver.session() as session:
            session.run(query, {
                "sid": feedback.session_id,
                "tbid": feedback.tessera_base_id,
                "uid": feedback.user_id,
                "fid": feedback.id,
                "color": feedback.color,
                "motivation": feedback.motivation,
                "now": feedback.created_at.isoformat()
            })
            return True
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        return False

async def get_session_feedback(session_id: str) -> List[Dict[str, Any]]:
    driver = get_driver()
    query = """
    MATCH (s:VotingSession {id: $sid})-[:COLLECTED]->(f:Feedback)
    MATCH (u:User)-[:GAVE_FEEDBACK]->(f)
    RETURN f.tessera_base_id as tessera_base_id, f.color as color, f.motivation as motivation, u.id as user_id, u.name as user_name
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"sid": session_id})
            return [dict(record) for record in result]
    except Exception as e:
        logger.error(f"Error getting session feedback: {e}")
        return []

async def submit_ranking(ranking: Ranking) -> bool:
    driver = get_driver()
    query = """
    MATCH (s:VotingSession {id: $sid})
    MATCH (u:User {id: $uid})

    // Delete existing ranking for this tessera in this session
    OPTIONAL MATCH (u)-[old:RANKED]->(r_old:Ranking)
    WHERE r_old.session_id = $sid AND r_old.tessera_base_id = $tbid
    DETACH DELETE r_old

    MERGE (r:Ranking {id: $rid})
    ON CREATE SET
        r.session_id = $sid,
        r.tessera_base_id = $tbid,
        r.category = $category,
        r.created_at = datetime($now)
    ON MATCH SET
        r.category = $category,
        r.updated_at = datetime($now)

    MERGE (u)-[:RANKED]->(r)
    MERGE (s)-[:COLLECTED]->(r)
    RETURN r.id
    """
    try:
        with driver.session() as session:
            session.run(query, {
                "sid": ranking.session_id,
                "tbid": ranking.tessera_base_id,
                "uid": ranking.user_id,
                "rid": ranking.id,
                "category": ranking.category,
                "now": ranking.created_at.isoformat()
            })
            return True
    except Exception as e:
        logger.error(f"Error submitting ranking: {e}")
        return False

async def get_session_rankings(session_id: str) -> List[Dict[str, Any]]:
    driver = get_driver()
    query = """
    MATCH (s:VotingSession {id: $sid})-[:COLLECTED]->(r:Ranking)
    RETURN r.tessera_base_id as tessera_base_id, r.category as category, count(r) as count
    ORDER BY count DESC
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"sid": session_id})
            return [dict(record) for record in result]
    except Exception as e:
        logger.error(f"Error getting session rankings: {e}")
        return []

async def update_session_stage(session_id: str, stage: str) -> bool:
    driver = get_driver()
    query = """
    MATCH (s:VotingSession {id: $sid})
    SET s.stage = $stage
    RETURN s.id
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"sid": session_id, "stage": stage})
            return result.single() is not None
    except Exception as e:
        logger.error(f"Error updating session stage: {e}")
        return False

async def get_eligible_claims_for_ranking(session_id: str) -> List[Dict[str, Any]]:
    """
    Returns tessera_base_ids that have had no objections (red feedback) in the refinement phase.
    """
    driver = get_driver()
    query = """
    MATCH (s:VotingSession {id: $sid})
    MATCH (s)-[:COLLECTED]->(f:Feedback)
    WITH f.tessera_base_id as tessera_base_id, collect(f.color) as colors
    WHERE NOT 'red' IN colors
    RETURN DISTINCT tessera_base_id
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"sid": session_id})
            return [dict(record) for record in result]
    except Exception as e:
        logger.error(f"Error getting eligible claims: {e}")
        return []

async def get_consent_shortlist(session_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Calculates the shortlist based on Phase 2a rankings and thresholds.
    Drempels:
    - Positive: >= 40% in 'high' OR >= 60% in 'high' + 'medium'
    - Rejected: >= 30% in 'discard'
    - Contested: In between
    """
    driver = get_driver()
    query = """
    MATCH (s:VotingSession {id: $sid})
    MATCH (s)-[:COLLECTED]->(r:Ranking)
    WITH r.tessera_base_id as tessera_base_id,
         count(r) as total_votes,
         count(CASE WHEN r.category = 'high' THEN 1 END) as high_count,
         count(CASE WHEN r.category IN ['high', 'medium'] THEN 1 END) as combined_count,
         count(CASE WHEN r.category = 'discard' THEN 1 END) as discard_count
    WITH tessera_base_id, total_votes,
         (toFloat(high_count) / total_votes) as high_p,
         (toFloat(combined_count) / total_votes) as combined_p,
         (toFloat(discard_count) / total_votes) as discard_p

    // Check if current user voted consent on this tessera
    OPTIONAL MATCH (u:User {id: $uid})-[:VOTED_CONSENT]->(v:ConsentVote)
    WHERE v.session_id = $sid AND v.tessera_base_id = tessera_base_id

    RETURN tessera_base_id,
           CASE
               WHEN discard_p >= 0.3 THEN 'rejected'
               WHEN high_p >= 0.4 OR combined_p >= 0.6 THEN 'positive'
               ELSE 'contested'
           END as status,
           high_p, combined_p, discard_p,
           CASE WHEN v IS NOT NULL THEN v.vote ELSE null END as user_vote,
           CASE WHEN v IS NOT NULL THEN v.motivation ELSE null END as user_motivation
    ORDER BY high_p DESC, combined_p DESC
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"sid": session_id, "uid": user_id})
            return [dict(record) for record in result]
    except Exception as e:
        logger.error(f"Error getting consent shortlist: {e}")
        return []

from app.models.domain import ConsentVote

async def submit_consent_vote(vote: ConsentVote) -> bool:
    driver = get_driver()
    query = """
    MATCH (s:VotingSession {id: $sid})
    MATCH (u:User {id: $uid})

    // Delete existing consent vote for this tessera in this session
    OPTIONAL MATCH (u)-[old:VOTED_CONSENT]->(v_old:ConsentVote)
    WHERE v_old.session_id = $sid AND v_old.tessera_base_id = $tbid
    DETACH DELETE v_old

    MERGE (v:ConsentVote {id: $vid})
    ON CREATE SET
        v.session_id = $sid,
        v.tessera_base_id = $tbid,
        v.vote = $vote,
        v.motivation = $motivation,
        v.created_at = datetime($now)
    ON MATCH SET
        v.vote = $vote,
        v.motivation = $motivation,
        v.updated_at = datetime($now)

    MERGE (u)-[:VOTED_CONSENT]->(v)
    MERGE (s)-[:COLLECTED]->(v)
    RETURN v.id
    """
    try:
        with driver.session() as session:
            session.run(query, {
                "sid": vote.session_id,
                "tbid": vote.tessera_base_id,
                "uid": vote.user_id,
                "vid": vote.id,
                "vote": vote.vote,
                "motivation": vote.motivation,
                "now": vote.created_at.isoformat()
            })
            return True
    except Exception as e:
        logger.error(f"Error submitting consent vote: {e}")
        return False

async def mark_phase_completed(session_id: str, user_id: str, phase: str) -> bool:
    driver = get_driver()
    query = """
    MATCH (s:VotingSession {id: $sid})
    MATCH (u:User {id: $uid})
    MERGE (u)-[r:COMPLETED_PHASE {phase: $phase}]->(s)
    ON CREATE SET r.completed_at = datetime()
    ON MATCH SET r.completed_at = datetime()
    RETURN r
    """
    try:
        with driver.session() as session:
            session.run(query, {"sid": session_id, "uid": user_id, "phase": phase})
            return True
    except Exception as e:
        logger.error(f"Error marking phase completed: {e}")
        return False

async def get_session_participation(session_id: str) -> List[Dict[str, Any]]:
    """
    Returns a list of participants and their activity status for the given session.
    """
    driver = get_driver()
    query = """
    MATCH (s:VotingSession {id: $sid})<-[:HAS_SESSION]-(ds:DesignSpace)
    MATCH (u:User)-[:HAS_ROLE]->(ds)

    WITH DISTINCT u, s

    OPTIONAL MATCH (u)-[:GAVE_FEEDBACK]->(f:Feedback) WHERE f.session_id = $sid
    OPTIONAL MATCH (u)-[:RANKED]->(r:Ranking) WHERE r.session_id = $sid
    OPTIONAL MATCH (u)-[:VOTED_CONSENT]->(v:ConsentVote) WHERE v.session_id = $sid

    // Check for explicit completion
    OPTIONAL MATCH (u)-[c_refine:COMPLETED_PHASE {phase: 'refine'}]->(s)
    OPTIONAL MATCH (u)-[c_ranking:COMPLETED_PHASE {phase: 'ranking'}]->(s)
    OPTIONAL MATCH (u)-[c_consent:COMPLETED_PHASE {phase: 'consent'}]->(s)

    RETURN u.email as email,
           coalesce(u.name, u.email) as name,
           u.id as user_id,
           count(DISTINCT f) > 0 as has_feedback,
           count(DISTINCT r) > 0 as has_ranking,
           count(DISTINCT v) > 0 as has_consent,
           c_refine IS NOT NULL as has_completed_refinement,
           c_ranking IS NOT NULL as has_completed_ranking,
           c_consent IS NOT NULL as has_completed_consent,
           count(DISTINCT f) as feedback_count
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"sid": session_id})
            return [dict(record) for record in result]
    except Exception as e:
        logger.error(f"Error getting session participation: {e}")
        return []

async def finalize_deliberation(session_id: str, user_id: str) -> Dict[str, Any]:
    """Sluit de deliberatiesessie af en registreert de consensus in de DesignSpace."""
    from app.db.sessions import get_session_context

    driver = get_driver()

    issue_id, project_id = await get_session_context(session_id)
    if not issue_id:
        return {"status": "error", "message": "Context niet gevonden"}

    try:
        query_close = """
        MATCH (s:VotingSession {id: $sid})
        SET s.status = 'closed', s.stage = 'closed', s.ended_at = datetime()
        RETURN s.id AS id
        """
        with driver.session() as sess:
            sess.run(query_close, {"sid": session_id})

        return {"status": "success", "session_id": session_id}

    except Exception as e:
        logger.error(f"Error finalizing deliberation: {e}")
        return {"status": "error", "message": str(e)}

async def validate_phase_transition(session_id: str, current_stage: str, target_stage: str) -> Dict[str, Any]:
    """
    Validates if a transition to the target stage is allowed based on collected data.
    Returns:
        {
            "allowed": bool,
            "type": "success" | "warning" | "error",
            "message": str
        }
    """
    driver = get_driver()

    # 1. Refine -> Ranking
    if target_stage == 'ranking':
        query = """
        MATCH (s:VotingSession {id: $sid})
        OPTIONAL MATCH (s)-[:COLLECTED]->(f:Feedback)
        RETURN count(f) as count
        """
        with driver.session() as session:
            count = session.run(query, {"sid": session_id}).single()["count"]

        if count == 0:
            return {
                "allowed": True, # Non-blocking warning
                "type": "warning",
                "message": "Er is nog geen feedback gegeven. Weet je zeker dat je wilt doorgaan?"
            }

    # 2. Ranking -> Consent (STRICT GATEKEEPER)
    if target_stage == 'consent':
        query = """
        MATCH (s:VotingSession {id: $sid})
        OPTIONAL MATCH (s)-[:COLLECTED]->(r:Ranking)
        RETURN count(r) as count
        """
        with driver.session() as session:
            count = session.run(query, {"sid": session_id}).single()["count"]

        if count == 0:
            return {
                "allowed": False, # BLOCKING
                "type": "error",
                "message": "Kan niet naar Consent-fase: Minstens 1 deelnemer moet kandidaten prioriteren."
            }

    # 3. Consent -> Closed (Finalize) (STRICT GATEKEEPER)
    if target_stage == 'closed':
        query = """
        MATCH (s:VotingSession {id: $sid})
        OPTIONAL MATCH (s)-[:COLLECTED]->(v:ConsentVote)
        RETURN count(v) as count
        """
        with driver.session() as session:
            count = session.run(query, {"sid": session_id}).single()["count"]

        if count == 0:
             return {
                "allowed": False,
                "type": "error",
                "message": "Kan sessie niet sluiten: Geen stemmen uitgebracht in de Consent-fase."
            }

    return {"allowed": True, "type": "success", "message": "Gereed voor volgende fase."}
