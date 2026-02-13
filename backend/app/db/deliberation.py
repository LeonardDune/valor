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
    MATCH (cv:ClaimVersion {id: $cvid})
    MATCH (u:User {id: $uid})
    
    // Delete existing feedback from this user for this claim in this session
    OPTIONAL MATCH (u)-[old:GAVE_FEEDBACK]->(f_old:Feedback)-[:ON_CLAIM]->(cv)
    WHERE f_old.session_id = $sid
    DETACH DELETE f_old
    
    CREATE (f:Feedback {
        id: $fid,
        session_id: $sid,
        color: $color,
        motivation: $motivation,
        created_at: datetime($now)
    })
    CREATE (u)-[:GAVE_FEEDBACK]->(f)
    CREATE (f)-[:ON_CLAIM]->(cv)
    CREATE (s)-[:COLLECTED]->(f)
    RETURN f.id
    """
    try:
        with driver.session() as session:
            session.run(query, {
                "sid": feedback.session_id,
                "cvid": feedback.claim_version_id,
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
    MATCH (s:VotingSession {id: $sid})-[:COLLECTED]->(f:Feedback)-[:ON_CLAIM]->(cv:ClaimVersion)
    MATCH (u:User)-[:GAVE_FEEDBACK]->(f)
    RETURN cv.id as claim_version_id, f.color as color, f.motivation as motivation, u.id as user_id, u.name as user_name
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
    MATCH (cv:ClaimVersion {id: $cvid})
    MATCH (u:User {id: $uid})
    
    // Delete existing ranking
    OPTIONAL MATCH (u)-[old:RANKED]->(r_old:Ranking)-[:RANKED_CLAIM]->(cv)
    WHERE r_old.session_id = $sid
    DETACH DELETE r_old
    
    CREATE (r:Ranking {
        id: $rid,
        session_id: $sid,
        category: $category,
        created_at: datetime($now)
    })
    CREATE (u)-[:RANKED]->(r)
    CREATE (r)-[:RANKED_CLAIM]->(cv)
    CREATE (s)-[:COLLECTED]->(r)
    RETURN r.id
    """
    try:
        with driver.session() as session:
            session.run(query, {
                "sid": ranking.session_id,
                "cvid": ranking.claim_version_id,
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
    MATCH (s:VotingSession {id: $sid})-[:COLLECTED]->(r:Ranking)-[:RANKED_CLAIM]->(cv:ClaimVersion)
    RETURN cv.id as claim_version_id, r.category as category, count(r) as count
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
    Returns claims that have had NOprincipally objections (red feedback) in the refinement phase.
    """
    driver = get_driver()
    query = """
    MATCH (s:VotingSession {id: $sid})
    MATCH (s)-[:COLLECTED]->(f:Feedback)-[:ON_CLAIM]->(cv:ClaimVersion)
    WITH cv, collect(f.color) as colors
    WHERE NOT 'red' IN colors
    RETURN DISTINCT cv.id as id, cv.statement as statement, cv.polarity as polarity, cv.confidence as confidence
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
    MATCH (s:VotingSession {id: $sid})-[:COLLECTED]->(r:Ranking)-[:RANKED_CLAIM]->(cv:ClaimVersion)
    WITH cv, 
         count(r) as total_votes,
         count(CASE WHEN r.category = 'high' THEN 1 END) as high_count,
         count(CASE WHEN r.category IN ['high', 'medium'] THEN 1 END) as combined_count,
         count(CASE WHEN r.category = 'discard' THEN 1 END) as discard_count
    WITH cv, total_votes,
         (toFloat(high_count) / total_votes) as high_p,
         (toFloat(combined_count) / total_votes) as combined_p,
         (toFloat(discard_count) / total_votes) as discard_p
    
    // Check if current user voted
    OPTIONAL MATCH (u:User {id: $uid})-[:VOTED_CONSENT]->(v:ConsentVote)-[:VOTE_ON]->(cv)
    WHERE v.session_id = $sid
    
    RETURN cv.id as id, 
           cv.statement as statement,
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
    MATCH (cv:ClaimVersion {id: $cvid})
    MATCH (u:User {id: $uid})
    
    // Delete existing consent vote
    OPTIONAL MATCH (u)-[old:VOTED_CONSENT]->(v_old:ConsentVote)-[:VOTE_ON]->(cv)
    WHERE v_old.session_id = $sid
    DETACH DELETE v_old
    
    CREATE (v:ConsentVote {
        id: $vid,
        session_id: $sid,
        vote: $vote,
        motivation: $motivation,
        created_at: datetime($now)
    })
    CREATE (u)-[:VOTED_CONSENT]->(v)
    CREATE (v)-[:VOTE_ON]->(cv)
    CREATE (s)-[:COLLECTED]->(v)
    RETURN v.id
    """
    try:
        with driver.session() as session:
            session.run(query, {
                "sid": vote.session_id,
                "cvid": vote.claim_version_id,
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

async def get_session_participation(session_id: str) -> List[Dict[str, Any]]:
    """
    Returns a list of participants and their activity status for the given session.
    """
    driver = get_driver()
    query = """
    MATCH (s:VotingSession {id: $sid})<-[:HAS_SESSION]-(tv:ThemeVersion)<-[:HAS_VERSION]-(t:Theme)
    
    // 1. Get all emails from Invites OR Users with roles on the theme
    OPTIONAL MATCH (i:Invite)-[:FOR_ACCESS]->(t)
    WITH s, t, collect(DISTINCT i.email) as invited_emails
    
    OPTIONAL MATCH (u:User)-[:HAS_ROLE]->(t)
    WITH s, t, invited_emails, collect(DISTINCT u.email) as role_emails
    
    WITH s, t, [e IN (invited_emails + role_emails) WHERE e IS NOT NULL] as all_emails
    UNWIND all_emails as email
    
    // 2. Resolve to User where possible
    OPTIONAL MATCH (u:User {email: email})
    
    // 3. Activity counts
    OPTIONAL MATCH (u)-[:GAVE_FEEDBACK]->(f:Feedback) WHERE f.session_id = $sid
    WITH email, u, count(DISTINCT f) as feedback_count, s, t
    
    OPTIONAL MATCH (u)-[:RANKED]->(r:Ranking) WHERE r.session_id = $sid
    WITH email, u, feedback_count, count(DISTINCT r) as ranking_count, s, t
    
    OPTIONAL MATCH (u)-[:VOTED_CONSENT]->(v:ConsentVote) WHERE v.session_id = $sid
    WITH email, u, feedback_count, ranking_count, count(DISTINCT v) as consent_count
    
    RETURN DISTINCT email,
           coalesce(u.name, email) as name,
           u.id as user_id,
           feedback_count > 0 as has_feedback,
           ranking_count > 0 as has_ranking,
           consent_count > 0 as has_consent
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"sid": session_id})
            return [dict(record) for record in result]
    except Exception as e:
        logger.error(f"Error getting session participation: {e}")
        return []

async def finalize_deliberation(session_id: str, user_id: str) -> Dict[str, Any]:
    """
    Finalizes the deliberation: 
    1. Determines consensus from voting results.
    2. Reuses crud.create_decision to snapshot the ThemeVersion (cloning factors/claims).
    3. Integrates accepted new claims/proposals into the new version.
    """
    from app.db.sessions import get_session_context
    from app.db.crud import create_decision
    
    driver = get_driver()
    
    # 1. Resolve Context
    theme_id, _ = await get_session_context(session_id)
    if not theme_id:
        return {"status": "error", "message": "Context niet gevonden"}

    try:
        # 2. CREATE SNAPSHOT (Reusing working logic for Deep Copy)
        # This creates new_tv, clones Factors, clones existing Claims.
        new_version_id = await create_decision(
            theme_id=theme_id,
            description=f"Besluit na sessie {session_id}",
            author_id=user_id
        )
        
        # 3. APPLY SESSION DELTA (Consensus)
        # We need to:
        # a. Mark clones of rejected claims as historical? 
        #    Actually, create_decision copies EVERYTHING active.
        #    If the session had proposals, we need to ADD the accepted ones.
        
        query_apply_consensus = """
        MATCH (s:VotingSession {id: $sid})
        MATCH (new_tv:ThemeVersion {id: $nvid})
        SET s.status = 'closed', s.stage = 'closed'
        
        WITH s, new_tv
        
        // Find all claims discussed in this session
        OPTIONAL MATCH (s)-[:COLLECTED]->(v:ConsentVote)-[:VOTE_ON]->(sess_cv:ClaimVersion)
        WITH s, new_tv, sess_cv, 
             count(CASE WHEN v.vote = 'approve' THEN 1 END) as approvals,
             count(CASE WHEN v.vote = 'object' THEN 1 END) as objections
        
        // Strategy: Prune and Apply
        // 1. Identify all claims that were part of this session's deliberation
        WITH s, new_tv, collect({
            cv: sess_cv,
            is_accepted: (approvals > 0 AND objections = 0)
        }) as session_results
        
        UNWIND session_results as result
        WITH s, new_tv, result.cv as sess_cv, result.is_accepted as is_accepted
        WHERE sess_cv IS NOT NULL
        
        // 2. Remove the Snapshot Clone for EVERY claim that was in the session
        // (If it's rejected, it stays gone. If it's accepted, we'll re-add a fresh version below)
        OPTIONAL MATCH (new_tv)-[:HAS_CLAIM]->(clone:ClaimVersion {base_id: sess_cv.base_id})
        DETACH DELETE clone
        
        // 3. Re-create ONLY the accepted ones
        WITH s, new_tv, sess_cv, is_accepted
        WHERE is_accepted = true
        
        CREATE (final_cv:ClaimVersion {
            id: randomUUID(),
            base_id: sess_cv.base_id,
            statement: sess_cv.statement,
            polarity: sess_cv.polarity,
            confidence: sess_cv.confidence,
            valid_from: datetime(),
            created_at: datetime()
        })
        CREATE (new_tv)-[:HAS_CLAIM]->(final_cv)
        
        // Link to ClaimBase (Identity)
        WITH final_cv, sess_cv, new_tv
        MATCH (cb:ClaimBase {id: sess_cv.base_id})
        MERGE (cb)-[:HAS_VERSION]->(final_cv)
        
        // Structural Re-wiring (Source/Target Factors)
        WITH final_cv, sess_cv, new_tv
        MATCH (sess_cv)<-[:CLAIMS]-(old_f_source:FactorVersion)
        MATCH (new_tv)-[:HAS_FACTOR]->(new_f_source:FactorVersion)
        WHERE new_f_source.base_id = old_f_source.base_id
        CREATE (new_f_source)-[:CLAIMS]->(final_cv)
        
        WITH final_cv, sess_cv, new_tv
        MATCH (sess_cv)-[:TO]->(old_f_target:FactorVersion)
        MATCH (new_tv)-[:HAS_FACTOR]->(new_f_target:FactorVersion)
        WHERE new_f_target.base_id = old_f_target.base_id
        CREATE (final_cv)-[:TO]->(new_f_target)
        
        RETURN count(final_cv) as applied_count
        """
        
        with driver.session() as sess:
            sess.run(query_apply_consensus, {"sid": session_id, "nvid": new_version_id})
            
        return {"status": "success", "next_version_id": new_version_id}

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
        
        # We might want to allow force-close if really stuck, but for now strict.
        # Actually, let's make it a warning if manual finalized via update_stage, 
        # but finalize_deliberation endpoint might have its own checks.
        # The user dashboard calls 'finalize' endpoint for Consent->Closed.
        # This validator is mostly for the 'Advance Stage' button logic.
        
        if count == 0:
             return {
                "allowed": False,
                "type": "error",
                "message": "Kan sessie niet sluiten: Geen stemmen uitgebracht in de Consent-fase."
            }

    return {"allowed": True, "type": "success", "message": "Gereed voor volgende fase."}
