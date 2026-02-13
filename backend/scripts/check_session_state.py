import asyncio
from app.db.utils import get_driver
import json

async def check_state():
    driver = get_driver()
    with driver.session() as session:
        # 1. Check active sessions
        print("--- ACTIEVE SESSIES ---")
        res = session.run("MATCH (s:VotingSession) RETURN s.id, s.status, s.stage, s.created_at ORDER BY s.created_at DESC LIMIT 5")
        for rec in res:
            print(f"ID: {rec['s.id']} | Status: {rec['s.status']} | Stage: {rec['s.stage']} | Created: {rec['s.created_at']}")

        # 2. Check participation logic for the most recent session
        res = session.run("MATCH (s:VotingSession) RETURN s.id ORDER BY s.created_at DESC LIMIT 1")
        rec = res.single()
        if rec:
            sid = rec['s.id']
            print(f"\n--- PARTICIPATIE CHECK VOOR {sid} ---")
            
            # Count Invites
            inv_res = session.run("MATCH (s:VotingSession {id: $sid})<-[:HAS_SESSION]-(tv:ThemeVersion)<-[:HAS_VERSION]-(t:Theme)<-[:FOR_ACCESS]-(i:Invite) RETURN count(i)", {"sid": sid})
            print(f"Invites gevonden (via Theme): {inv_res.single()[0]}")
            
            # Count Roles
            role_res = session.run("MATCH (s:VotingSession {id: $sid})<-[:HAS_SESSION]-(tv:ThemeVersion)<-[:HAS_VERSION]-(t:Theme)<-[:HAS_ROLE]-(u:User) RETURN count(u)", {"sid": sid})
            # Wait, relationship is (User)-[:HAS_ROLE]->(Theme)?
            role_res = session.run("MATCH (s:VotingSession {id: $sid})<-[:HAS_SESSION]-(tv:ThemeVersion)<-[:HAS_VERSION]-(t:Theme)<-[r:HAS_ROLE]-(u:User) RETURN count(u)", {"sid": sid})
            # Let's check direction in schema
            print(f"Directe Theme Roles gevonden: {role_res.single()[0]}")
            
            # Better check: (User)-[:HAS_ROLE]->(Theme)
            role_res_rev = session.run("MATCH (u:User)-[:HAS_ROLE]->(t:Theme)<-[:HAS_VERSION]-(tv:ThemeVersion)-[:HAS_SESSION]->(s:VotingSession {id: $sid}) RETURN count(u)", {"sid": sid})
            print(f"Directe Theme Roles (rev direction) gevonden: {role_res_rev.single()[0]}")

        # 3. Check specific Stage 'closed' vs 'Closed'
        res = session.run("MATCH (s:VotingSession) WHERE s.stage IN ['closed', 'Closed'] RETURN s.id, s.stage")
        for rec in res:
            print(f"Sessie {rec['s.id']} heeft stage: '{rec['s.stage']}'")

if __name__ == '__main__':
    asyncio.run(check_state())
