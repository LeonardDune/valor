
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path so we can import 'app'
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Load .env (ensure we use the dev one)
# In Docker, env vars are often already set, but loading .env helps if running manually
# Path inside docker (/app/.env)
load_dotenv(".env")

from app.db.crud import create_theme, create_space, create_conversation_thread, get_spaces_by_theme, get_threads_by_space, get_project_users
from app.db.utils import get_driver

async def verify():
    print("🚀 Starting Space Model Verification...")
    
    driver = get_driver()
    
    # 0. Ensure Constraint (Quick fix since we didn't run a migration script)
    with driver.session() as session:
         session.run("CREATE CONSTRAINT space_id IF NOT EXISTS FOR (s:Space) REQUIRE s.id IS NODE KEY")
         print("✅ Constraint ensured.")

    # 1. Setup Data
    print("1. Creating Test Hierarchy...")
    try:
        # Create Project directly via cypher to avoid dependency issues or just use crud if easy
        with driver.session() as session:
             pid = "proj-test-verify"
             session.run("""
             MERGE (o:Organization {id: 'org-dev-valor'})
             MERGE (p:Project {id: $pid})
             ON CREATE SET p.name = 'Verification Project', p.status='active'
             MERGE (o)-[:OWNS]->(p)
             """, pid=pid)
             print(f"   Project: {pid}")
             
             # 2. Create Theme via CRUD
             tid = await create_theme(pid, "Verificatie Thema", "Test Thema voor Space Model")
             print(f"   Theme Created: {tid}")
             
             # 3. Create Space
             sid = await create_space(tid, "Debat Ruimte", "Een ruimte voor debat")
             print(f"   Space Created: {sid}")
             
             # 4. Create Thread
             thid = await create_conversation_thread(sid, "Is dit een test?")
             print(f"   Thread Created: {thid}")
             
             # 5. Verify Retrieval
             print("\n2. Verifying Retrieval...")
             spaces = await get_spaces_by_theme(tid)
             print(f"   Spaces in Theme: {len(spaces)}")
             assert len(spaces) >= 1
             assert spaces[0]['id'] == sid
             print("   ✅ get_spaces_by_theme OK")
             
             threads = await get_threads_by_space(sid)
             print(f"   Threads in Space: {len(threads)}")
             assert len(threads) >= 1
             assert threads[0]['id'] == thid
             print("   ✅ get_threads_by_space OK")
             
             print("\n🎉 Verification SUCCESS! The Space Datamodel is functional.")
             
    except Exception as e:
        print(f"\n❌ Verification FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify())
