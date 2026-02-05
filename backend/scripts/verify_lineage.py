import asyncio
import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.crud import create_user, create_organization, create_project, create_theme, create_decision, get_theme_versions_by_theme
from app.db.utils import get_driver

async def verify_lineage():
    print("Starting Lineage Verification...")
    
    # 1. Setup
    print("1. Setting up Hierarchy...")
    user_id = "lineage-test-user"
    
    try:
        await create_user("lineage@example.com", "Lineage Tester", user_id)
    except Exception:
        pass # User might exist
    
    org_id = await create_organization("Lineage Org", "Test Org", user_id)
    proj_id = await create_project("Lineage Project", org_id, "Test Project", user_id)
    
    # Use a unique name to avoid collisions
    import uuid
    unique_suffix = str(uuid.uuid4())[:8]
    theme_name = f"Lineage Theme {unique_suffix}"
    
    theme_id = await create_theme(proj_id, theme_name, "Testing Lineage", user_id)
    print(f"   Theme Created: {theme_id} ({theme_name})")

    # 2. Verify Initial Version has NO derived_from
    print("2. Verifying Initial Version Lineage...")
    versions = await get_theme_versions_by_theme(theme_id, user_id)
    v1 = versions[0]
    print(f"   V1: {v1['name']}, derived_from: {v1.get('derived_from_id')}")
    assert v1.get('derived_from_id') is None

    # 3. Create Decision (Snapshot V1 -> V2)
    print("3. Creating Decision (Snapshotting V1 -> V2)...")
    v2_id = await create_decision(theme_id, "Snapshot V1", user_id)
    print(f"   V2 Created: {v2_id}")

    # 4. Verify V2 is derived from V1
    print("4. Verifying V2 Lineage...")
    versions = await get_theme_versions_by_theme(theme_id, user_id)
    
    # Find v2 and v1 in the list
    v2 = next(v for v in versions if v['id'] == v2_id)
    v1_check = next(v for v in versions if v['id'] == v1['id'])
    
    print(f"   V2 derived_from: {v2.get('derived_from_id')}")
    print(f"   V1 ID: {v1['id']}")
    
    assert v2.get('derived_from_id') == v1['id']
    print("   ✅ V2 is correctly marked as derived from V1")

    # 5. Create Another Decision (Snapshot V2 -> V3)
    print("5. Creating Decision (Snapshotting V2 -> V3)...")
    v3_id = await create_decision(theme_id, "Snapshot V2", user_id)
    
    # 6. Verify V3 is derived from V2
    print("6. Verifying V3 Lineage...")
    versions = await get_theme_versions_by_theme(theme_id, user_id)
    v3 = next(v for v in versions if v['id'] == v3_id)
    
    print(f"   V3 derived_from: {v3.get('derived_from_id')}")
    # v3 should be derived from v2_id
    assert v3.get('derived_from_id') == v2_id
    print("   ✅ V3 is correctly marked as derived from V2")
    
    print("🎉 LINEAGE VERIFIED SUCCESSFULLY.")

if __name__ == "__main__":
    asyncio.run(verify_lineage())
