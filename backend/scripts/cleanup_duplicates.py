import asyncio
from app.db.utils import get_driver, close_driver

async def cleanup_duplicates():
    driver = get_driver()
    query = """
    MATCH (t:ThemeBase)-[r:HAS_VERSION]->(v:ThemeVersion)
    WITH t, v, collect(r) as rels
    WHERE size(rels) > 1
    // Keep the one with the lowest ID (or just the first one)
    FOREACH (r IN tail(rels) | DELETE r)
    RETURN count(t) as processed_themes
    """
    try:
        with driver.session() as session:
            result = session.run(query)
            count = result.single()["processed_themes"]
            print(f"Cleaned up duplicates for {count} themes.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        close_driver()

if __name__ == "__main__":
    asyncio.run(cleanup_duplicates())
