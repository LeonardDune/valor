import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../app'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from app.main import app
from app.db.utils import verify_connectivity, close_driver
from app.auth import verify_token

# Mock Auth using Dependency Override
def mock_verify_token():
    return {
        "sub": "admin-uid", 
        "email": "admin@valor.com", 
        "user_metadata": {
            "full_name": "Admin User", 
            "is_platform_admin": True
        }
    }

# Apply override
app.dependency_overrides[verify_token] = mock_verify_token

client = TestClient(app)

def test_active_version_flow():
    print("--- Starting API Verification ---")
    # No headers needed due to override
    headers = {}
    
    # 1. Create Organization (if needed, but usually default exists)
    # create_new_organization handled by startup_migration or existing
    # Let's just assume we can create a project under a new Org to be clean
    
    response = client.post("/organizations", json={"name": "API Test Org", "description": "Temp"}, headers=headers)
    if response.status_code == 200:
        org_id = response.json()["id"]
        print(f"Created Org: {org_id}")
    else:
        # Check if list returns one
        orgs = client.get("/organizations", headers=headers).json()
        org_id = orgs[0]['id']
        print(f"Using Existing Org: {org_id}")

    # 2. Create Project
    response = client.post("/projects", json={"name": "API Test Project", "organization_id": org_id}, headers=headers)
    assert response.status_code == 200, f"Create Project failed: {response.text}"
    project_id = response.json()["id"]
    print(f"Created Project: {project_id}")

    # 3. Create Theme
    response = client.post(f"/projects/{project_id}/themes", json={"project_id": project_id, "name": "API Test Theme"}, headers=headers)
    assert response.status_code == 200, f"Create Theme failed: {response.text}"
    theme_id = response.json()["id"]
    print(f"Created Theme: {theme_id}")

    # 4. Create ThemeVersion
    response = client.post(f"/themes/{theme_id}/versions", json={"name": "Version 1", "description": "Initial Version"}, headers=headers)
    assert response.status_code == 200, f"Create Version failed: {response.text}"
    version_id = response.json()["id"]
    print(f"Created Version: {version_id}")

    # 5. Get Active Version
    print("Fetching Active Version...")
    response = client.get(f"/themes/{theme_id}/active-version", headers=headers)
    assert response.status_code == 200, f"Get Active Version failed: {response.text}"
    data = response.json()
    
    print(f"Active Version Data: {data}")
    
    
    assert data["id"] == version_id
    assert data["name"] == "Version 1"
    
    print(">>> Active Version OK.")
    
    # 6. Create Factor (Manual)
    print("Creating Factor...")
    factor_resp = client.post("/factors", json={
        "name": "Test Factor A", 
        "description": "Desc A", 
        "type": "systeemelement",
        "theme_id": theme_id
    }, headers=headers)
    assert factor_resp.status_code == 200, f"Create Factor failed: {factor_resp.text}"
    factor_id = factor_resp.json()["id"]
    print(f"Created Factor: {factor_id} (Base ID)")

    # 7. Create Another Factor
    factor_resp2 = client.post("/factors", json={
        "name": "Test Factor B", 
        "theme_id": theme_id
    }, headers=headers)
    factor_id2 = factor_resp2.json()["id"]

    # 8. Create Claim (Manual)
    print("Creating Claim...")
    claim_resp = client.post("/claims_manual", json={
        "theme_id": theme_id,
        "source_id": factor_id,
        "target_id": factor_id2,
        "statement": "A influences B",
        "polarity": "+",
        "confidence": 0.8
    }, headers=headers)
    assert claim_resp.status_code == 200, f"Create Claim failed: {claim_resp.text}"
    
    # 9. Verify Retrieval
    print("Verifying Factor Retrieval (Legacy Endpoint -> Active Version)...")
    get_factors = client.get(f"/themes/{theme_id}/factors", headers=headers)
    assert get_factors.status_code == 200
    factors = get_factors.json()
    print(f"Factors Found: {len(factors)}")
    assert len(factors) >= 2
    assert any(f["id"] == factor_id for f in factors)
    
    print("Verifying Claim Retrieval (Legacy Endpoint -> Active Version)...")
    get_claims = client.get(f"/themes/{theme_id}/claims", headers=headers)
    assert get_claims.status_code == 200
    claims = get_claims.json()
    print(f"Claims Found: {len(claims)}")
    assert len(claims) >= 1
    assert claims[0]["source_id"] == factor_id
    assert claims[0]["target_id"] == factor_id2
    
    print(">>> VERIFICATION SUCCESS: Factor/Claim Retrieval via Active Version works.")

if __name__ == "__main__":
    # We need to ensure DB is connected for the app to work within TestClient context roughly
    # Actually TestClient expects app to handle startup.
    # But we might need to verify connectivity first.
    with TestClient(app) as local_client:
        # Force startup event? TestClient calls lifespan.
        test_active_version_flow()
