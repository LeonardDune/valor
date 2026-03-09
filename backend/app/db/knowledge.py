from typing import List, Optional, Dict
import uuid
import logging

from app.db.utils import get_driver
from app.models.domain import Claim

logger = logging.getLogger(__name__)


# --- ID Resolution ---

async def get_project_id_by_factor(factor_id: str) -> Optional[str]:
    driver = get_driver()
    query = """
    MATCH (p:Project)-[:HAS_THEME]->(t)-[:HAS_FACTOR]->(f)
    WHERE f.id = $fid
    RETURN p.id as pid
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"fid": factor_id})
            record = result.single()
            return record["pid"] if record else None
    except Exception as e:
        logger.error(f"Error resolving project for factor {factor_id}: {e}")
        return None


async def get_project_id_by_claim(claim_id: str) -> Optional[str]:
    driver = get_driver()
    query = """
    MATCH (p:Project)-[:HAS_THEME]->(t)-[:HAS_VERSION]->(tv)-[:HAS_FACTOR]->(fv)-[:CLAIMS]->(cv)<-[:HAS_VERSION]-(cb:ClaimBase {id: $id})
    RETURN p.id as pid
    """
    try:
        with driver.session() as session:
            result = session.run(query, {"id": claim_id})
            record = result.single()
            return record["pid"] if record else None
    except Exception as e:
        logger.error(f"Error resolving project for claim {claim_id}: {e}")
        return None


# --- Factors ---

async def get_factors_for_version(version_id: str) -> List[Dict]:
    """
    Get all FactorVersions associated with a specific ThemeVersion.
    Returns list of dicts formatted for API response (using Base ID as 'id').
    """
    driver = get_driver()
    query = """
    MATCH (tv:ThemeVersion {id: $vid})
    MATCH (tv)-[r:HAS_FACTOR]->(fv:FactorVersion)
    OPTIONAL MATCH (fv)-[:HAS_THREAD]->(t:ConversationThread)
    RETURN DISTINCT {
        id: fv.base_id,              // Frontend expects Identity ID
        version_id: fv.id,           // Specific Version ID
        name: fv.name,
        description: fv.description,
        type: r.role,                // Fetched from relationship
        theme_id: fv.theme_id,       // If encoded in FactorVersion, or we omit
        thread_id: t.id
    } as factor
    """
    with driver.session() as session:
        return [r["factor"] for r in session.run(query, {"vid": version_id})]


async def get_factors_for_theme(theme_id: str) -> List[Dict]:
    """
    Legacy/Active Wrapper: Get factors for the ACTIVE ThemeVersion.
    """
    driver = get_driver()
    query = """
    MATCH (t:ThemeBase {id: $tid})-[:HAS_VERSION]->(tv:ThemeVersion)
    WHERE tv.status = 'active' AND tv.valid_to IS NULL
    RETURN tv.id as vid
    """
    with driver.session() as session:
        result = session.run(query, {"tid": theme_id}).single()
        if result:
            return await get_factors_for_version(result["vid"])
        return []


async def create_factor_manual(name: str, description: Optional[str], type: str, theme_id: str, author_id: str) -> str:
    """
    Creates a FactorBase + FactorVersion.
    Links Base to User (Author).
    Links Version to Active ThemeVersion.
    """
    driver = get_driver()
    fid = str(uuid.uuid4())
    vid = str(uuid.uuid4())

    query = """
    MATCH (t:ThemeBase {id: $tid})
    MATCH (u:User {id: $uid})

    // 1. Find Active ThemeVersion
    MATCH (t)-[:HAS_VERSION]->(tv:ThemeVersion)
    WHERE tv.status = 'active' AND tv.valid_to IS NULL

    WITH DISTINCT t, u, tv

    // 2. Create FactorBase
    CREATE (fb:FactorBase {
        id: $fid,
        created_at: datetime(),
        created_by: $uid
    })
    CREATE (u)-[:CREATED]->(fb)
    CREATE (t)-[:HAS_FACTOR]->(fb)

    // 3. Create FactorVersion
    CREATE (fv:FactorVersion {
        id: $vid,
        base_id: $fid,
        name: $name,
        description: $desc,
        // type removed - now context-dependent on relationship
        version_id: tv.id,
        created_at: datetime(),
        valid_from: datetime(),
        valid_to: NULL
    })
    CREATE (fb)-[:HAS_VERSION]->(fv) // Base -> Version
    CREATE (tv)-[:HAS_FACTOR {role: $type}]->(fv)

    RETURN fb.id as id // Return Base ID to be consistent with "Entity Identity"
    """

    with driver.session() as session:
        result = session.run(query, {
            "fid": fid,
            "vid": vid,
            "name": name,
            "desc": description,
            "type": type,
            "tid": theme_id,
            "uid": author_id
        })
        record = result.single()
        if not record:
            raise ValueError(f"Theme {theme_id} not found or has no active version.")
        return record["id"]


async def update_factor_manual(factor_id: str, name: Optional[str], description: Optional[str], type: Optional[str], theme_id: Optional[str]):
    driver = get_driver()

    if not theme_id:
        # Fallback/Legacy Attempt: Update by ID directly if it's a legacy Factor node
        query = """
        MATCH (f:FactorBase {id: $id})
        SET f.name = coalesce($name, f.name),
            f.description = coalesce($desc, f.description),
            f.type = coalesce($type, f.type)
        """
        with driver.session() as session:
            session.run(query, {"id": factor_id, "name": name, "desc": description, "type": type})
        return

    # Versioned Update
    query = """
    MATCH (t:ThemeBase {id: $tid})
    MATCH (t)-[:HAS_VERSION]->(tv:ThemeVersion)
    WHERE tv.status = 'active' AND tv.valid_to IS NULL

    MATCH (fb:FactorBase {id: $fid})
    MATCH (tv)-[rel:HAS_FACTOR]->(fv:FactorVersion)
    WHERE fv.base_id = fb.id

    SET fv.name = coalesce($name, fv.name),
        fv.description = coalesce($desc, fv.description),
        rel.role = coalesce($type, rel.role)
    """
    with driver.session() as session:
        session.run(query, {"fid": factor_id, "tid": theme_id, "name": name, "desc": description, "type": type})


async def delete_factor_manual(factor_id: str):
    driver = get_driver()
    query = """
    MATCH (fb:FactorBase {id: $id})
    MATCH (fb)-[:HAS_VERSION]->(fv:FactorVersion)
    MATCH (tv:ThemeVersion)-[:HAS_FACTOR]->(fv)
    WHERE tv.status = 'active' AND tv.valid_to IS NULL
    DETACH DELETE fv
    """
    with driver.session() as session:
        session.run(query, {"id": factor_id})


# --- Claims ---

async def get_claims_for_version(version_id: str) -> List[Claim]:
    """
    Get all ClaimVersions visible in this ThemeVersion.
    Traverses: ThemeVersion -> FactorVersions -> Claims
    """
    driver = get_driver()
    query = """
    MATCH (tv:ThemeVersion {id: $vid})
    MATCH (tv)-[:HAS_FACTOR]->(fv_source:FactorVersion)
    MATCH (fv_source)-[rel:CLAIMS]->(cv:ClaimVersion)-[:TO]->(fv_target:FactorVersion)
    MATCH (cb:ClaimBase)-[:HAS_VERSION]->(cv) // Retrieve Base for immutable props

    // Optional threads for claim, source and target
    OPTIONAL MATCH (cv)-[:HAS_THREAD]->(t_claim:ConversationThread)
    OPTIONAL MATCH (fv_source)-[:HAS_THREAD]->(t_source:ConversationThread)
    OPTIONAL MATCH (fv_target)-[:HAS_THREAD]->(t_target:ConversationThread)

    // Ensure target is also in this version (Consistency Check)
    WHERE (tv)-[:HAS_FACTOR]->(fv_target)

    RETURN DISTINCT {
        id: cv.base_id,          // Identity
        version_id: cv.id,       // State
        statement: cv.statement,
        polarity: cv.polarity,
        confidence: cv.confidence,
        evidence_text: cv.evidence_text,
        evidence_url: cv.evidence_url,
        status: cv.status,

        source_id: fv_source.base_id,
        target_id: fv_target.base_id,
        source_version_id: fv_source.id,
        target_version_id: fv_target.id,

        claim_thread_id: t_claim.id,
        source_thread_id: t_source.id,
        target_thread_id: t_target.id,

        created_at: toString(cv.created_at),
        created_by: cb.created_by  // Immutable Creator
    } as claim
    """

    with driver.session() as session:
        results = session.run(query, {"vid": version_id})
        claims = []
        for record in results:
            c = record["claim"]
            try:
                claims.append(Claim(**c))
            except Exception as e:
                logger.warning(f"Invalid claim data for {c.get('id')}: {e}")
        return claims


async def get_claims_for_theme(theme_id: str) -> List[Claim]:
    """
    Legacy/Active Wrapper: Get claims for the ACTIVE ThemeVersion.
    """
    driver = get_driver()
    query = """
    MATCH (t:ThemeBase {id: $tid})-[:HAS_VERSION]->(tv:ThemeVersion)
    WHERE tv.status = 'active' AND tv.valid_to IS NULL
    RETURN tv.id as vid
    """
    with driver.session() as session:
        result = session.run(query, {"tid": theme_id}).single()
        if result:
            return await get_claims_for_version(result["vid"])
        return []


async def create_claim_manual(theme_id: str, source_id: str, target_id: str, statement: str, author_id: str, polarity: str = "+", confidence: float = 1.0, evidence_text: Optional[str] = None, evidence_url: Optional[str] = None) -> str:
    """
    Creates ClaimBase + ClaimVersion.
    Resolves Source/Target Base IDs to their Active Versions in the current Theme Version.
    """
    driver = get_driver()
    cid = str(uuid.uuid4())
    vid = str(uuid.uuid4())

    query = """
    MATCH (theme:ThemeBase {id: $thid})
    MATCH (u:User {id: $uid})

    // 1. Find Active ThemeVersion
    MATCH (theme)-[:HAS_VERSION]->(tv:ThemeVersion)
    WHERE tv.status = 'active' AND tv.valid_to IS NULL

    // 2. Resolve Source/Target Factors (Base -> Active Version)
    MATCH (tv)-[:HAS_FACTOR]->(fv_source:FactorVersion {base_id: $sid})
    MATCH (tv)-[:HAS_FACTOR]->(fv_target:FactorVersion {base_id: $tid})

    WITH DISTINCT theme, u, tv, fv_source, fv_target

    // 3. Create ClaimBase
    CREATE (cb:ClaimBase {
        id: $cid,
        created_at: datetime(),
        created_by: $uid
    })
    CREATE (u)-[:CREATED]->(cb)

    // 4. Create ClaimVersion
    CREATE (cv:ClaimVersion {
        id: $vid,
        base_id: $cid,
        statement: $stmt,
        polarity: $pol,
        confidence: $conf,
        evidence_text: $ev_txt,
        evidence_url: $ev_url,
        source_version_id: fv_source.id,
        target_version_id: fv_target.id,
        created_at: datetime(),
        valid_from: datetime(),
        valid_to: NULL
    })
    CREATE (cb)-[:HAS_VERSION]->(cv) // Base -> Version

    // 5. Link ClaimVersion to FactorVersions
    CREATE (fv_source)-[:CLAIMS]->(cv)
    CREATE (cv)-[:TO]->(fv_target)

    RETURN cb.id as id // Return Base ID
    """

    with driver.session() as session:
        result = session.run(query, {
            "cid": cid,
            "vid": vid,
            "sid": source_id,
            "tid": target_id,
            "stmt": statement,
            "pol": polarity,
            "conf": confidence,
            "ev_txt": evidence_text,
            "ev_url": evidence_url,
            "thid": theme_id,
            "uid": author_id
        })
        record = result.single()
        if not record:
            raise ValueError("Could not create claim. Ensure Theme and Factors exist and are active in the current version.")
        return record["id"]


async def update_claim_manual(claim_id: str, statement: Optional[str], polarity: Optional[str], confidence: Optional[float], source_id: Optional[str], target_id: Optional[str], evidence_text: Optional[str] = None, evidence_url: Optional[str] = None):
    driver = get_driver()
    query = """
    MATCH (cb:ClaimBase {id: $id})
    MATCH (cb)-[:HAS_VERSION]->(cv:ClaimVersion)
    WHERE cv.valid_to IS NULL
    SET cv.statement = coalesce($stmt, cv.statement),
        cv.polarity = coalesce($pol, cv.polarity),
        cv.confidence = coalesce($conf, cv.confidence),
        cv.evidence_text = CASE WHEN $ev_txt_provided THEN $ev_txt ELSE cv.evidence_text END,
        cv.evidence_url = CASE WHEN $ev_url_provided THEN $ev_url ELSE cv.evidence_url END
    """
    with driver.session() as session:
        session.run(query, {
            "id": claim_id,
            "stmt": statement,
            "pol": polarity,
            "conf": confidence,
            "ev_txt": evidence_text,
            "ev_url": evidence_url,
            "ev_txt_provided": evidence_text is not None,
            "ev_url_provided": evidence_url is not None
        })


async def delete_claim_manual(claim_id: str):
    driver = get_driver()
    query = """
    MATCH (cb:ClaimBase {id: $id})
    MATCH (cb)-[:HAS_VERSION]->(cv:ClaimVersion)
    WHERE cv.valid_to IS NULL
    DETACH DELETE cv
    """
    with driver.session() as session:
        session.run(query, {"id": claim_id})
