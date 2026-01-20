import asyncio
import os
import sys
import logging
import uuid
import requests

# Add backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Check if server is running? Or just use requests locally if running?
# Ideally we should use TestClient for integration without running server, 
# but for verification script usually we want to test effectively.
# Let's simple use TestClient from starlette/fastapi which is faster/easier.

from fastapi.testclient import TestClient
from app.main import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = TestClient(app)

def verify_111():
    logger.info("--- Verifying Story #111: Proposal API ---")

    # 1. Create a User (Author)
    # We need a user to be the author
    test_uid = f"user_{str(uuid.uuid4())[:8]}"
    
    # 2. Create Proposal
    proposal_data = {
        "title": f"Test Proposal {test_uid}",
        "description": "This is a verification proposal",
        "author_id": "test_user_id_verify"
    }
    
    # Need to ensure author exists? CRUD create_proposal checks?
    # Yes, our CRUD creates a relationship to User. So we must create user first using CRUD directly or API.
    # Let's use CRUD directly to setup dependencies to be safe, or just mock?
    # Our CRUD throws exception if user not found. So we MUST create user.
    # But this script runs outside the async loop if using TestClient? 
    # TestClient calls the app. The app uses async CRUD.
    
    # We need to pre-seed data.
    # Let's make this script Async and use CRUD to seed, then TestClient (sync) to test API.
    
    pass

async def seed_and_verify():
    from app.db.crud import create_user
    test_email = f"verifier_{uuid.uuid4()}@test.com"
    author_id = await create_user(test_email, "Verifier")
    
    logger.info(f"Seeded Author: {author_id}")

    # Now use Client
    # 1. Create Proposal
    payload = {
        "title": "API Verification Proposal",
        "description": "Created via API",
        "author_id": author_id
    }
    
    response = client.post("/proposals/", json=payload)
    if response.status_code == 200:
        pid = response.json()
        logger.info(f"PASS: Created Proposal ID: {pid}")
    else:
        logger.error(f"FAIL: Create Proposal returned {response.status_code}: {response.text}")
        return

    # 2. Get Proposals
    response = client.get(f"/proposals/?author={author_id}")
    if response.status_code == 200:
        proposals = response.json()
        if len(proposals) >= 1 and proposals[0]['id'] == pid:
            logger.info(f"PASS: Retrieved Proposal list. Found {len(proposals)} proposals.")
        else:
            logger.error(f"FAIL: Proposal list mismatch. Found {len(proposals)}")
    else:
        logger.error(f"FAIL: Get Proposals returned {response.status_code}")

    # 3. Get Single Proposal
    response = client.get(f"/proposals/{pid}")
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'draft':
            logger.info("PASS: Fetched single proposal, status is 'draft'")
        else:
             logger.error(f"FAIL: Proposal status is {data['status']}")
    else:
        logger.error(f"FAIL: Get Single Proposal returned {response.status_code}")


    # 4. Update Status
    update_payload = {"status": "proposed"}
    response = client.put(f"/proposals/{pid}/status", json=update_payload)
    if response.status_code == 200:
        logger.info("PASS: Update Status to 'proposed' successful")
    else:
        logger.error(f"FAIL: Update Status returned {response.status_code}")
        
    # Verify update
    response = client.get(f"/proposals/{pid}")
    if response.json()['status'] == 'proposed':
        logger.info("PASS: Status verification successful")
    else:
        logger.error("FAIL: Status was not updated persistedly")

    logger.info("--- Verification 111 Complete ---")

if __name__ == "__main__":
    asyncio.run(seed_and_verify())
