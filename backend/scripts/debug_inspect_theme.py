
import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../app'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.utils import get_driver, verify_connectivity, close_driver

async def inspect_theme(theme_id):
    await verify_connectivity()
    driver = get_driver()
    
    query = """
    MATCH (t:Theme {id: $tid})
    OPTIONAL MATCH (t)-[r]->(related)
    RETURN t.id, type(r), related.id, labels(related)
    """
    
    print(f"--- Inspecting Theme: {theme_id} ---")
    with driver.session() as session:
        result = session.run(query, {"tid": theme_id})
        found = False
        for record in result:
             found = True
             print(f"Theme {record[0]} -[{record[1]}]-> {record[3]} ({record[2]})")
        
        if not found:
            print("!!! Theme NOT FOUND in DB !!!")

    close_driver()

if __name__ == "__main__":
    target_id = "fa874a61-82ea-41f5-adc7-55b692e1c409"
    asyncio.run(inspect_theme(target_id))
