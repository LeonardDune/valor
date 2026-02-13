import asyncio
import os
import sys
# Ensure app is in path
sys.path.append(os.getcwd())

from app.db.utils import get_driver

async def verify_db_state():
    driver = get_driver()
    
    print(f"{'VERSION ID':<38} | {'NAME':<30} | {'STATUS':<10} | {'FACTORS'}")
    print("-" * 100)
    
    query = """
    MATCH (t:Theme)-[:HAS_VERSION]->(tv:ThemeVersion)
    OPTIONAL MATCH (tv)-[:HAS_FACTOR]->(fv:FactorVersion)
    RETURN tv.id as id, tv.name as name, tv.status as status, tv.created_at as created_at, count(fv) as factors
    ORDER BY created_at DESC
    """
    
    with driver.session() as session:
        result = session.run(query)
        for record in result:
            print(f"{record['id']:<38} | {record['name']:<30} | {record['status']:<10} | {record['factors']}")

if __name__ == "__main__":
    asyncio.run(verify_db_state())
