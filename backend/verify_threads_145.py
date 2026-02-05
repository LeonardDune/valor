import asyncio
import uuid
import sys
import os

# Ensure backend path is in sys.path
# Ensure root path is in sys.path
sys.path.append('/app')

from app.db.crud import create_conversation_thread, get_threads_by_target
from app.db.utils import get_driver

async def run_verification():
    print("Starting verification for US #145...")
    
    target_id = str(uuid.uuid4())
    print(f"Target ID (mock): {target_id}")
    
    driver = get_driver()
    
    # 1. Create Generic Target Node
    with driver.session() as session:
        session.run("CREATE (n:TestNode {id: $id, name: 'Test Target'})", {"id": target_id})
        print("Created generic TestNode.")

    # 2. Create Thread
    topic = "Test Polymorphic Thread"
    print(f"Creating thread with topic: {topic}")
    tid = await create_conversation_thread(target_id, topic)
    print(f"Thread created with ID: {tid}")

    # 3. Get Threads
    print("Retrieving threads...")
    threads = await get_threads_by_target(target_id)
    print(f"Threads found: {threads}")
    
    # Assertions
    if len(threads) != 1:
        print(f"FAILURE: Expected 1 thread, found {len(threads)}")
        sys.exit(1)
        
    if threads[0]['topic'] != topic:
        print(f"FAILURE: Expected topic '{topic}', found '{threads[0]['topic']}'")
        sys.exit(1)
        
    if threads[0]['id'] != tid:
        print(f"FAILURE: Expected ID '{tid}', found '{threads[0]['id']}'")
        sys.exit(1)
        
    print("Assertions PASSED.")
    
    # 4. Cleanup
    with driver.session() as session:
        session.run("MATCH (n:TestNode {id: $id}) DETACH DELETE n", {"id": target_id})
        session.run("MATCH (t:ConversationThread {id: $tid}) DETACH DELETE t", {"tid": tid})
        print("Cleanup complete.")

    print("VERIFICATION SUCCESSFUL!")

if __name__ == "__main__":
    asyncio.run(run_verification())
