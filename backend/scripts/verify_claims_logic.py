import asyncio
import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.utils import get_driver
from app.db.crud import get_claims_for_theme, get_theme_versions_by_theme

async def verify():
    driver = get_driver()
    theme_name = "Test Theme"
    user_id = "cb15ab85-7267-42c3-a3ba-71313c71fb74" # rl.wouters ID
    
    print(f"🕵️ Verifying Claims Logic for '{theme_name}'...")
    
    with driver.session() as session:
        # Get Theme ID
        t = session.run("MATCH (t:Theme {name: $name}) RETURN t.id", {"name": theme_name}).single()
        if not t:
            print("❌ Theme not found")
            return
        theme_id = t['t.id']
        print(f"✅ Theme ID: {theme_id}")

        # 1. API Logic: get_claims_for_theme (Active Version)
        print("\n--- 1. Testing get_claims_for_theme (Active) ---")
        try:
            claims = await get_claims_for_theme(theme_id)
            print(f"   API returned {len(claims)} claims.")
            for c in claims:
                print(f"   - Claim: {c.statement} ({c.id}) | Source: {c.source_version_id} -> Target: {c.target_version_id}")
        except Exception as e:
            print(f"   ❌ ERROR calling get_claims_for_theme: {e}")

        # 2. Check Versions
        print("\n--- 2. Checking Versions ---")
        versions = await get_theme_versions_by_theme(theme_id, user_id)
        for v in versions:
            print(f"   Version {v['name']} ({v['id']}) Status: {v['status']}")
            
            # Check Claims for this specific version logic
            print(f"   -> Fetching claims for version {v['id']}...")
            try:
                # We need to import get_claims_for_version
                from app.db.crud import get_claims_for_version
                v_claims = await get_claims_for_version(v['id'])
                print(f"      Count: {len(v_claims)}")
            except Exception as e:
                print(f"      ❌ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
