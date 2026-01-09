import asyncio
from app.db.utils import get_driver

async def migrate_ids():
    driver = get_driver()
    # Find all factors without IDs and give them one
    query = """
    MATCH (f:Factor) 
    WHERE f.id IS NULL 
    SET f.id = randomUUID() 
    RETURN count(f) as count
    """
    try:
        with driver.session() as session:
            result = session.run(query)
            record = result.single()
            print(f"Successfully migrated {record['count']} nodes.")
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    asyncio.run(migrate_ids())
