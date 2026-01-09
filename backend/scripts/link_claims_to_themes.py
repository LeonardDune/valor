from app.db.utils import get_driver
import asyncio
import os

async def link_factors():
    driver = get_driver()
    # Link factors that appear in claims to the theme they belong to
    query = """
    MATCH (t:Theme)<-[:BELONGS_TO]-(thread:ConversationThread)-[:GENERATED]->(c:Claim)
    MATCH (s:Factor)-[:CLAIMS]-(c)-[:TO]->(target:Factor)
    WITH t, s, target
    MERGE (t)-[:HAS_FACTOR]->(s)
    MERGE (t)-[:HAS_FACTOR]->(target)
    RETURN count(distinct s) + count(distinct target) as count
    """
    try:
        with driver.session() as session:
            result = session.run(query)
            count = result.single()["count"]
            print(f"Linked {count} factors to their themes.")
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    os.environ["NEO4J_URI"] = "bolt://localhost:7687"
    os.environ["NEO4J_USER"] = "neo4j"
    os.environ["NEO4J_PASSWORD"] = "password"
    asyncio.run(link_factors())
