import asyncio
import os
import sys
import argparse
from dotenv import load_dotenv

# Add parent dir to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Load env explicitly if needed, though utils does it too
load_dotenv()

from app.db.utils import get_driver, close_driver, verify_connectivity

async def migrate(dry_run=False):
    uri = os.getenv("NEO4J_URI", "UNKNOWN")
    print(f"🔌 Connecting to Neo4j at: {uri}")
    
    if dry_run:
        print("⚠️  DRY RUN MODE: No changes will be committed.")
    else:
        print("🚨 PRODUCTION MODE: Changes WILL be committed.")
        confirm = input("Are you sure you want to proceed? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            return

    print("Starting migration...")
    try:
        await verify_connectivity()
        driver = get_driver()
        
        # Query 1: Creators -> Admin Role
        query1_read = """
        MATCH (u:User)-[:CREATED]->(t:ThemeBase)-[:HAS_VERSION]->(v:ThemeVersion)
        WHERE v.status = 'active'
        AND NOT (u)-[:HAS_ROLE {role: 'admin'}]->(v)
        RETURN count(u) as candidates
        """
        
        query1_write = """
        MATCH (u:User)-[:CREATED]->(t:ThemeBase)-[:HAS_VERSION]->(v:ThemeVersion)
        WHERE v.status = 'active'
        MERGE (u)-[:HAS_ROLE {role: 'admin'}]->(v)
        RETURN count(u) as fixed_creators
        """
        
        # Query 2: Theme Members -> Version Role
        query2_read = """
        MATCH (u:User)-[r:HAS_ROLE]->(t:ThemeBase)-[:HAS_VERSION]->(v:ThemeVersion)
        WHERE v.status = 'active'
        AND NOT (u)-[:HAS_ROLE {role: r.role}]->(v)
        RETURN count(u) as candidates
        """
        
        query2_write = """
        MATCH (u:User)-[r:HAS_ROLE]->(t:ThemeBase)-[:HAS_VERSION]->(v:ThemeVersion)
        WHERE v.status = 'active'
        MERGE (u)-[:HAS_ROLE {role: r.role}]->(v)
        RETURN count(u) as fixed_members
        """
        
        with driver.session() as session:
            print("\n--- Fixing Creators ---")
            candidates1 = session.run(query1_read).single()['candidates']
            print(f"Found {candidates1} creators needing role migration.")
            
            if not dry_run and candidates1 > 0:
                result1 = session.run(query1_write).single()
                print(f"✅ Fixed {result1['fixed_creators']} creators.")
            elif dry_run:
                print(f"ℹ️  [Dry Run] Would fix {candidates1} creators.")

            print("\n--- Fixing Members ---")
            candidates2 = session.run(query2_read).single()['candidates']
            print(f"Found {candidates2} members needing role migration.")
            
            if not dry_run and candidates2 > 0:
                result2 = session.run(query2_write).single()
                print(f"✅ Fixed {result2['fixed_members']} members.")
            elif dry_run:
                print(f"ℹ️  [Dry Run] Would fix {candidates2} members.")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
    finally:
        close_driver()
        print("\nDone.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Migrate participation roles.')
    parser.add_argument('--dry-run', action='store_true', help='Simulate migration without changes')
    args = parser.parse_args()
    
    asyncio.run(migrate(dry_run=args.dry_run))
