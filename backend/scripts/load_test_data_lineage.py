import asyncio
import os
import sys
import uuid
import datetime

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.utils import get_driver
from app.db.crud import (
    create_organization, 
    create_project, 
    create_theme, 
    create_decision,
    get_theme_versions_by_theme
)

async def load_test_data():
    print("🚀 Starting Lineage Test Data Load...")
    driver = get_driver()
    
    # 1. Wipe Database (Keep Users)
    print("1. 🧹 Wiping Database (Preserving Users)...")
    await wipe_db_keep_users(driver)
    
    # 2. Setup User 'rl.wouters'
    print("2. 👤 Setting up User 'rl.wouters'...")
    # REAL User ID from DB Dump
    user_id = "cb15ab85-7267-42c3-a3ba-71313c71fb74" 
    email = "rl.wouters@gmail.com"
    
    await ensure_user(driver, user_id, email, "rl.wouters")
    
    # 3. Create Org / Project / Theme
    print("3. 🏗️ Creating Hierarchy (Test Org -> Project -> Theme)...")
    org_id = await create_organization("Test Org", "Een test organisatie voor lineage verificatie", user_id)
    proj_id = await create_project("Test Project", org_id, "Project voor validatie", user_id)
    
    # Create Theme and ensuring Base has name (for dashboard compatibility)
    theme_name = "Test Theme"
    theme_id = await create_theme(proj_id, theme_name, "Theme met versie historie", user_id)
    
    # PATCH: Set name on ThemeBase for Dashboard visibility
    await set_theme_base_name(driver, theme_id, theme_name)
    print(f"   Theme Created: {theme_id}")
    
    # 4. Add Content to V1 (Active)
    print("4. 📝 Adding Content to Version 1...")
    versions = await get_theme_versions_by_theme(theme_id, user_id)
    v1 = versions[0] # The active version created by create_theme
    v1_id = v1['id']
    print(f"   V1 ID: {v1_id}")

    # Create Factors in V1 (Pass user_id)
    f1_id = await create_test_factor(driver, v1_id, "Factor A", "Concept", user_id)
    f2_id = await create_test_factor(driver, v1_id, "Factor B", "Driver", user_id)
    
    # Create Claim in V1 (Pass user_id)
    await create_test_claim(driver, v1_id, f1_id, f2_id, "Causes", 0.8, user_id)
    
    # 5. Snapshot V1 -> V2
    print("5. 📸 Snapshotting V1 -> V2 (Decision)...")
    v2_id = await create_decision(theme_id, "Decision 1: Baseline established", user_id)
    print(f"   V2 Created: {v2_id}")
    
    # 6. Add Content to V2
    print("6. 📝 Adding Content to Version 2...")
    # Find the NEW factor IDs in V2 that correspond to old factors (needed for linking)
    # But for simplicity, let's just create a NEW distinct factor in V2
    f3_id = await create_test_factor(driver, v2_id, "Factor C (New in V2)", "Outcome", user_id)
    
    # 7. Snapshot V2 -> V3
    print("7. 📸 Snapshotting V2 -> V3 (Decision)...")
    v3_id = await create_decision(theme_id, "Decision 2: Added Outcome Factor", user_id)
    print(f"   V3 Created: {v3_id}")
    
    print("✅ Test Data Loaded Successfully!")
    print(f"   User: {email} (ID: {user_id})")
    print(f"   Theme: Test Theme ({theme_id})")

async def wipe_db_keep_users(driver):
    query = """
    MATCH (n)
    WHERE NOT n:User AND NOT n:Migration
    DETACH DELETE n
    """
    with driver.session() as session:
        session.run(query)

async def ensure_user(driver, user_id, email, name):
    query = """
    MERGE (u:User {email: $email})
    SET u.id = $uid, u.name = $name, u.is_platform_admin = true
    RETURN u.id
    """
    with driver.session() as session:
        session.run(query, {"uid": user_id, "email": email, "name": name})

async def create_test_factor(driver, version_id, name, type, user_id):
    fid = str(uuid.uuid4())
    base_id = str(uuid.uuid4())
    query = """
    MATCH (v:ThemeVersion {id: $vid})
    
    CREATE (fb:FactorBase {id: $bid, created_at: datetime(), created_by: $uid})
    
    CREATE (f:FactorVersion {
        id: $fid,
        base_id: $bid,
        name: $name,
        type: $type,
        description: 'Test Factor',
        version_id: $vid,
        created_at: datetime(),
        valid_from: datetime()
    })
    CREATE (v)-[:HAS_FACTOR]->(f)
    CREATE (fb)-[:HAS_VERSION]->(f)
    RETURN f.id as id
    """
    with driver.session() as session:
        return session.run(query, {
            "vid": version_id, "fid": fid, "bid": base_id, "name": name, "type": type, "uid": user_id
        }).single()["id"]

async def create_test_claim(driver, version_id, source_id, target_id, statement, confidence, user_id):
    cid = str(uuid.uuid4())
    base_id = str(uuid.uuid4())
    query = """
    MATCH (s:FactorVersion {id: $sid})
    MATCH (t:FactorVersion {id: $tid})
    
    CREATE (cb:ClaimBase {id: $bid, created_at: datetime(), created_by: $uid})
    
    CREATE (c:ClaimVersion {
        id: $cid,
        base_id: $bid,
        statement: $stmt,
        confidence: $conf,
        polarity: 'positive',
        source_version_id: $sid,
        target_version_id: $tid,
        created_at: datetime(),
        valid_from: datetime()
    })
    CREATE (s)-[:CLAIMS]->(c)
    CREATE (c)-[:TO]->(t)
    CREATE (cb)-[:HAS_VERSION]->(c)
    """
    with driver.session() as session:
        session.run(query, {
            "cid": cid, "bid": base_id, "sid": source_id, "tid": target_id, 
            "stmt": statement, "conf": confidence, "uid": user_id
        })

async def set_theme_base_name(driver, theme_id, name):
    query = "MATCH (t:Theme:ThemeBase {id: $tid}) SET t.name = $name"
    with driver.session() as session:
        session.run(query, {"tid": theme_id, "name": name})

if __name__ == "__main__":
    asyncio.run(load_test_data())
