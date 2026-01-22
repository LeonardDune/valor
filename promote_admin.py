import asyncio
import os
import sys
from neo4j import GraphDatabase

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.utils import get_driver

async def promote_user(user_email_partial: str):
    driver = get_driver()
    print(f"Attempting to promote user matching: {user_email_partial}")
    
    query = """
    MATCH (u:User)
    WHERE u.email CONTAINS $email OR u.id = $email
    SET u.is_platform_admin = true
    RETURN u.email, u.id, u.name
    """
    
    try:
        with driver.session() as session:
            result = session.run(query, {"email": user_email_partial})
            record = result.single()
            if record:
                print(f"SUCCESS: Promoted {record['u.name']} ({record['u.email']}) to Platform Admin.")
            else:
                print("FAILURE: User not found.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    # Target specific users found in the DB dump
    targets = ["rl.wouters@gmail.com", "admin@valor.local"]
    
    import asyncio
    
    async def run_migrations():
        for t in targets:
            await promote_user(t)
            
    asyncio.run(run_migrations())
