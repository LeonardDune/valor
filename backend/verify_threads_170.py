import asyncio
import sys
import os
import uuid
from typing import List, Dict

# Ensure we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.utils import get_driver, verify_connectivity
from app.db.crud import create_conversation_thread, get_threads_by_target, get_thread_counts, create_thread_message, get_thread_messages

async def verify_backend_170():
    print("--- Verifying Story #170 Backend ---")
    
    # 1. Check connectivity
    connected = await verify_connectivity()
    if not connected:
        print("Failed to connect to Neo4j")
        sys.exit(1)
    
    driver = get_driver()
    
    # 2. Setup Test Data (Create a dummy node)
    node_id = str(uuid.uuid4())
    print(f"Creating test node {node_id}...")
    with driver.session() as session:
        session.run("CREATE (n:TestNode {id: $id, name: 'Test Thread Target'}) RETURN n", {"id": node_id})
        
    try:
        # 3. Create Threads
        print("Creating threads...")
        t1 = await create_conversation_thread(node_id, "Discussion 1")
        t2 = await create_conversation_thread(node_id, "Discussion 2")
        print(f"Created threads: {t1}, {t2}")
        
        # 4. Verify Thread Counts
        print("Verifying thread counts...")
        counts = await get_thread_counts([node_id])
        print(f"Counts: {counts}")
        assert counts.get(node_id) == 2, f"Expected 2 threads, got {counts.get(node_id)}"
        
        # 5. Create Messages (Human only)
        print("Creating messages...")
        user_id = "user_123"
        msg1 = await create_thread_message(t1, user_id, "Hello world")
        msg2 = await create_thread_message(t1, user_id, "Reply to hello")
        print(f"Created messages: {msg1['id']}, {msg2['id']}")
        
        # 6. Verify Messages Retrieval
        print("Retrieving messages...")
        messages = await get_thread_messages(t1)
        print(f"Retrieved {len(messages)} messages")
        assert len(messages) == 2
        assert messages[0]['content'] == "Hello world"
        assert messages[1]['content'] == "Reply to hello"
        
        print("✅ Backend Verification Passed!")
        
    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        raise e
    finally:
        # Cleanup
        print("Cleaning up...")
        with driver.session() as session:
            session.run("MATCH (n:TestNode {id: $id}) DETACH DELETE n", {"id": node_id})
            session.run("MATCH (t:ConversationThread {id: $id}) DETACH DELETE t", {"id": t1})
            session.run("MATCH (t:ConversationThread {id: $id}) DETACH DELETE t", {"id": t2})

if __name__ == "__main__":
    asyncio.run(verify_backend_170())
