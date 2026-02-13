import uuid
import datetime
import asyncio
from app.db.utils import get_driver
from app.db.deliberation import finalize_deliberation

async def test_robust_pruning():
    driver = get_driver()
    
    # Target Theme
    t_id = "327853c6-1c1e-4e7e-b908-3e640fb19988" 
    u_id = "107e5861-774b-469e-b892-15256345f062" # Actual user ID from DB
    
    print(f"--- Starting Robust Pruning Test ---")
    
    with driver.session() as session:
        # 1. Find Current Active Version and its Claims
        find_q = """
        MATCH (t:Theme {id: $tid})-[:HAS_ACTIVE_VERSION]->(v:ThemeVersion)
        MATCH (v)-[:HAS_CLAIM]->(c:ClaimVersion)
        RETURN v.id as v_id, collect({id: c.id, base_id: c.base_id, statement: c.statement}) as claims
        """
        res = session.run(find_q, {"tid": t_id}).single()
        if not res or not res["claims"] or len(res["claims"]) < 3:
            print("ERROR: Theme must have at least 3 claims for this test.")
            return

        v1_id = res["v_id"]
        claims = res["claims"]
        print(f"Found Active Version: {v1_id} with {len(claims)} claims.")
        
        # Assign roles to claims for testing
        c_approved = claims[0]
        c_rejected = claims[1]
        c_discussed = claims[2]
        c_status_quo = claims[3] if len(claims) > 3 else None
        
        print(f"C1 (Approved):  {c_approved['statement']} ({c_approved['base_id']})")
        print(f"C2 (Rejected):  {c_rejected['statement']} ({c_rejected['base_id']})")
        print(f"C3 (Discussed): {c_discussed['statement']} ({c_discussed['base_id']})")
        if c_status_quo:
            print(f"C4 (StatusQuo): {c_status_quo['statement']} ({c_status_quo['base_id']})")

        # 2. Setup Session
        s_id = str(uuid.uuid4())
        setup_q = """
        MATCH (v:ThemeVersion {id: $v1_id})
        CREATE (s:VotingSession {
            id: $sid,
            status: 'active',
            stage: 'consent',
            created_at: datetime()
        })
        CREATE (v)-[:HAS_SESSION]->(s)
        
        WITH s
        MATCH (c1:ClaimVersion {id: $c1_id})
        MATCH (c2:ClaimVersion {id: $c2_id})
        MATCH (c3:ClaimVersion {id: $c3_id})
        
        // Activity 1: Consent Approval for C1
        CREATE (v1:ConsentVote {id: randomUUID(), session_id: $sid, vote: 'approve', created_at: datetime()})
        CREATE (s)-[:COLLECTED]->(v1)
        CREATE (v1)-[:VOTE_ON]->(c1)
        
        // Activity 2: Objection for C2
        CREATE (v2:ConsentVote {id: randomUUID(), session_id: $sid, vote: 'object', motivation: 'Rejected', created_at: datetime()})
        CREATE (s)-[:COLLECTED]->(v2)
        CREATE (v2)-[:VOTE_ON]->(c2)
        
        // Activity 3: Feedback Only for C3 (Discussed but no consensus)
        CREATE (f3:Feedback {id: randomUUID(), session_id: $sid, motivation: 'Just talking...', created_at: datetime()})
        CREATE (s)-[:COLLECTED]->(f3)
        CREATE (f3)-[:ON_CLAIM]->(c3)
        
        RETURN s.id
        """
        session.run(setup_q, {
            "v1_id": v1_id, 
            "sid": s_id,
            "c1_id": c_approved["id"],
            "c2_id": c_rejected["id"],
            "c3_id": c_discussed["id"]
        })
        print(f"Session {s_id} created with activity.")

        # 3. Finalize
        print("Finalizing...")
        result = await finalize_deliberation(s_id, u_id)
        if result["status"] == "error":
            print(f"FINALIZATION FAILED: {result['message']}")
            return
            
        new_v_id = result["next_version_id"]
        print(f"Finalization Success. New Version: {new_v_id}")

        # 4. Verify Results
        verify_q = """
        MATCH (v:ThemeVersion {id: $nvid})
        OPTIONAL MATCH (v)-[:HAS_CLAIM]->(c)
        RETURN count(c) as total, collect(c.base_id) as found_bases
        """
        res = session.run(verify_q, {"nvid": new_v_id}).single()
        found_bases = res["found_bases"]
        print(f"New version contains {res['total']} claims.")
        
        fail = False
        # Approved should be present
        if c_approved["base_id"] not in found_bases:
            print(f"FAIL: Approved claim {c_approved['base_id']} is missing!")
            fail = True
        # Rejected should be absent
        if c_rejected["base_id"] in found_bases:
            print(f"FAIL: Rejected claim {c_rejected['base_id']} is still present!")
            fail = True
        # Discussed/Unvoted should be absent
        if c_discussed["base_id"] in found_bases:
            print(f"FAIL: Discussed/Unvoted claim {c_discussed['base_id']} is still present!")
            fail = True
        # Status Quo should be present
        if c_status_quo and c_status_quo["base_id"] not in found_bases:
            print(f"FAIL: Status quo claim {c_status_quo['base_id']} is missing!")
            fail = True
            
        if not fail:
            print("\n✅ SUCCESS: Robust pruning logic verified!")
        else:
            print("\n❌ FAILED: Pruning logic issues detected.")

if __name__ == "__main__":
    asyncio.run(test_robust_pruning())

