from app.db.utils import get_driver
import asyncio
import os

async def migrate_themes():
    driver = get_driver()
    query = """
    MATCH (t:Theme)
    WHERE t.id IS NULL
    SET t.id = randomUUID()
    RETURN count(t) as count
    """
    try:
        with driver.session() as session:
            result = session.run(query)
            count = result.single()["count"]
            print(f"Migrated {count} themes.")
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    os.environ["NEO4J_URI"] = "bolt://localhost:7687"
    os.environ["NEO4J_USER"] = "neo4j"
    os.environ["NEO4J_PASSWORD"] = "password"
    asyncio.run(migrate_themes())
