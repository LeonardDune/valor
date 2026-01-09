from app.db.utils import get_driver
import asyncio
import os

async def rescue_factors():
    driver = get_driver()
    # Link any factor that doesn't have a HAS_FACTOR or is not part of a claim to the only theme
    query = """
    MATCH (t:Theme)
    WITH t
    MATCH (f:Factor)
    WHERE NOT (t)-[:HAS_FACTOR]->(f)
    MERGE (t)-[:HAS_FACTOR]->(f)
    RETURN count(f) as count
    """
    try:
        with driver.session() as session:
            result = session.run(query)
            count = result.single()["count"]
            print(f"Rescued {count} unlinked factors.")
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    os.environ["NEO4J_URI"] = "bolt://localhost:7687"
    os.environ["NEO4J_USER"] = "neo4j"
    os.environ["NEO4J_PASSWORD"] = "password"
    asyncio.run(rescue_factors())
