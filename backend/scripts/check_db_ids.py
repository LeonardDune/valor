import asyncio
from app.db.utils import get_driver

async def check_ids():
    driver = get_driver()
    query = "MATCH (f:Factor) WHERE f.id IS NULL RETURN count(f) as count"
    with driver.session() as session:
        result = session.run(query)
        record = result.single()
        print(f"Nodes without ID: {record['count']}")

if __name__ == "__main__":
    asyncio.run(check_ids())
