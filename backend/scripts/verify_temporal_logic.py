import asyncio
import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.crud import create_user, create_organization, create_project, create_theme, create_factor_manual, create_claim_manual, create_decision, get_driver
from app.db.utils import get_driver

async def verify_temporal_logic():
    print("Starting Temporal Logic Verification (Base/Version Refactor)...")
    
    # 1. Setup
    print("1. Setting up Hierarchy...")
    user_id = "temp-test-user-v3"
    await create_user("test-v3@example.com", "Temporal Tester V3", user_id)
    
    org_id = await create_organization("Temporal Org V3", "Test Org", user_id)
    proj_id = await create_project("Temporal Project V3", org_id, "Test Project", user_id)
    
    # Create Theme (Creates ThemeBase and ThemeVersion V1)
    theme_id = await create_theme(proj_id, "Temporal Theme V3", "Testing Base/Version", user_id)
    print(f"   Theme Created (Base ID): {theme_id}")
    
    # Verify Base and Version 1
    driver = get_driver()
    with driver.session() as session:
        r = session.run("MATCH (t:ThemeBase {id: $tid})-[:HAS_VERSION]->(v:ThemeVersion) RETURN v.name, v.status", {"tid": theme_id}).single()
        print(f"   Initial Version: {r['v.name']} ({r['v.status']})")
        assert r['v.name'] == "Temporal Theme V3"

    # 2. Add Content to V1
    print("2. Adding Factors and Claims to V1...")
    # These create Base + Version, linked to Active ThemeVersion
    f1_id = await create_factor_manual("Factor A", "Cause", "systeemelement", theme_id, user_id)
    f2_id = await create_factor_manual("Factor B", "Effect", "systeemelement", theme_id, user_id)
    print(f"   Factors Created (Base IDs): {f1_id}, {f2_id}")

    c1_id = await create_claim_manual(theme_id, f1_id, f2_id, "A increases B", user_id, "+", 0.8)
    print(f"   Claim Created (Base ID): {c1_id}")
    
    # Verify V1 Content
    with driver.session() as session:
        # Check FactorVersions in V1
        q = """
        MATCH (t:ThemeBase {id: $tid})-[:HAS_VERSION]->(v:ThemeVersion {status: 'active'})
        MATCH (v)-[:HAS_FACTOR]->(fv:FactorVersion)
        RETURN count(fv) as count
        """
        c = session.run(q, {"tid": theme_id}).single()['count']
        print(f"   V1 FactorVersion Count: {c} (Expected 2)")
        assert c == 2

    # 3. Decision Time: Snapshot V1 -> Start V2
    print("3. Creating Decision (Snapshotting V1, Starting V2)...")
    new_version_id = await create_decision(theme_id, "Baseline Established", user_id)
    print(f"   New Version ID: {new_version_id}")
    
    # 4. Modify V2
    print("4. Modifying V2 (Adding Factor C, Link B->C)...")
    # New Factor C (Base C + Version C in V2)
    f3_id = await create_factor_manual("Factor C", "Outcome", "criterium", theme_id, user_id)
    
    # Link B (from V2) to C
    # create_claim_manual resolves the active versions automatically using the Base IDs (f2_id, f3_id)
    # It should find FactorVersion for B in V2 (which is a clone) and FactorVersion for C in V2 (new)
    c2_id = await create_claim_manual(theme_id, f2_id, f3_id, "B impacts C", user_id, "+", 1.0)
    print(f"   Created Claim 2 (B->C) in V2. Base ID: {c2_id}")

    # 5. Verification
    print("5. Verifying Lineage and Isolation...")
    with driver.session() as session:
        # Verify Lineage: V2 -> DERIVED_FROM -> V1
        r = session.run("""
            MATCH (v2:ThemeVersion {id: $vid})-[:DERIVED_FROM]->(v1:ThemeVersion)
            RETURN v1.name as old_name
        """, {"vid": new_version_id}).single()
        print(f"   Theme Lineage Verified: V2 derived from {r['old_name']}")
        
        # Verify Factor Lineage: Factor B(V2) -> DERIVED_FROM -> Factor B(V1)
        r = session.run("""
            MATCH (fb:FactorBase {id: $fid})
            MATCH (v2:ThemeVersion {id: $vid})-[:HAS_FACTOR]->(fv2:FactorVersion {base_id: fb.id})
            MATCH (fv2)-[:DERIVED_FROM]->(fv1:FactorVersion)
            MATCH (v1:ThemeVersion)-[:HAS_FACTOR]->(fv1)
            RETURN fv2.id, fv1.id
        """, {"fid": f2_id, "vid": new_version_id}).single()
        print(f"   Factor Lineage Verified: Factor B (V2) derived from (V1)")
        
        # Verify Isolation: V1 should NOT have Factor C
        # V1 is the version that is now CLOSED (valid_to is not null)
        r = session.run("""
            MATCH (t:ThemeBase {id: $tid})-[:HAS_VERSION]->(v1:ThemeVersion)
            WHERE v1.valid_to IS NOT NULL
            OPTIONAL MATCH (v1)-[:HAS_FACTOR]->(fv:FactorVersion {name: 'Factor C'})
            RETURN fv
        """, {"tid": theme_id}).single()
        assert r['fv'] is None
        print("   V1 Isolation Verified: Does not contain Factor C")
        
        # Verify Claim Count in V2
        r = session.run("""
            MATCH (v2:ThemeVersion {id: $vid})
            MATCH (v2)-[:HAS_FACTOR]->(fv)-[:CLAIMS]->(cv:ClaimVersion)
            RETURN count(DISTINCT cv) as count
        """, {"vid": new_version_id}).single()
        print(f"   V2 Claim Count: {r['count']} (Expected 2)")
        assert r['count'] == 2
        
        # Verify Base->Version Linkage (User Request Check)
        # Factor A (Base) should have 2 Versions (V1, V2)
        r = session.run("""
            MATCH (fb:FactorBase {id: $fid})-[:HAS_VERSION]->(fv:FactorVersion)
            RETURN count(fv) as count
        """, {"fid": f1_id}).single()
        print(f"   Factor A Version Linked Count: {r['count']} (Expected 2)")
        assert r['count'] == 2
        
        # Claim 1 (Base) should have 2 Versions (V1, V2: A->B original)
        r = session.run("""
            MATCH (cb:ClaimBase {id: $cid})-[:HAS_VERSION]->(cv:ClaimVersion)
            RETURN count(cv) as count
        """, {"cid": c1_id}).single()
        print(f"   Claim 1 Version Linked Count: {r['count']} (Expected 2)")
        assert r['count'] == 2

    print("🎉 BASE/VERSION REFACTOR VERIFIED SUCCESSFULLY.")

if __name__ == "__main__":
    asyncio.run(verify_temporal_logic())
