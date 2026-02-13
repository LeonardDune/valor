import asyncio
from app.db.utils import get_driver

async def verify_versions():
    driver = get_driver()
    query = """
    MATCH (t:Theme)
    OPTIONAL MATCH (t)-[:HAS_VERSION]->(tv:ThemeVersion)
    OPTIONAL MATCH (tv)-[:HAS_FACTOR]->(fv:FactorVersion)
    RETURN t.name as theme, tv.id as version_id, tv.name as version_name, tv.status as status, count(fv) as factor_count
    ORDER BY tv.created_at DESC
    """
    
    print(f"{'THEME':<20} | {'VERSION NAME':<30} | {'STATUS':<10} | {'FACTORS'}")
    print("-" * 80)
    
    with driver.session() as session:
        result = session.run(query)
        for record in result:
            print(f"{record['theme']:<20} | {record['version_name']:<30} | {record['status']:<10} | {record['factor_count']}")

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.getcwd())
    asyncio.run(verify_versions())
