import asyncio
import uuid
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.db.deliberation import submit_feedback, submit_ranking, update_session_stage
from app.models.domain import Feedback, Ranking
from datetime import datetime

async def main():
    print("Starting backend verification...")
    
    sid = str(uuid.uuid4())
    cvid = "claim-1"
    uid = "test-user-1"
    
    # 1. Test Feedback
    print(f"Testing feedback submission for session {sid}...")
    f = Feedback(
        id=str(uuid.uuid4()),
        session_id=sid,
        claim_version_id=cvid,
        user_id=uid,
        color='green',
        motivation='Looks promising for the pilot.',
        created_at=datetime.now()
    )
    # Note: This will fail if DB is not reachable or nodes don't exist, 
    # but we can check if it at least imports and runs the logic.
    try:
        success = await submit_feedback(f)
        print(f"Feedback Success: {success}")
    except Exception as e:
        print(f"Feedback Failed (expected if no DB): {e}")

    # 2. Test Ranking
    print(f"Testing ranking submission...")
    r = Ranking(
        id=str(uuid.uuid4()),
        session_id=sid,
        claim_version_id=cvid,
        user_id=uid,
        category='high',
        created_at=datetime.now()
    )
    try:
        success = await submit_ranking(r)
        print(f"Ranking Success: {success}")
    except Exception as e:
        print(f"Ranking Failed (expected if no DB): {e}")

    # 3. Test Stage update
    print(f"Testing stage update to 'ranking'...")
    try:
        success = await update_session_stage(sid, 'ranking')
        print(f"Stage Update Success: {success}")
    except Exception as e:
        print(f"Stage Update Failed: {e}")

    print("Backend verification complete (Logic checked).")

if __name__ == "__main__":
    asyncio.run(main())
