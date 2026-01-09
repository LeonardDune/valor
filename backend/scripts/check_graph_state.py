from app.db.utils import get_driver
import asyncio
import os

async def check_graph():
    driver = get_driver()
    with driver.session() as session:
        # Check Themes
        print("--- Themes ---")
        themes = session.run("MATCH (t:Theme) RETURN t.id as id, t.name as name")
        for t in themes:
            print(f"Theme: {t['name']} (ID: {t['id']})")
        
        # Check Factors
        print("\n--- Factors ---")
        factors = session.run("MATCH (f:Factor) RETURN f.id as id, f.name as name, f.type as type")
        for f in factors:
            print(f"Factor: {f['name']} (Type: {f['type']}, ID: {f['id']})")
            
        # Check Relationships
        print("\n--- HAS_FACTOR Relationships ---")
        rels = session.run("MATCH (t:Theme)-[r:HAS_FACTOR]->(f:Factor) RETURN t.name as t_name, f.name as f_name")
        for r in rels:
            print(f"{r['t_name']} -> HAS_FACTOR -> {r['f_name']}")

if __name__ == "__main__":
    os.environ["NEO4J_URI"] = "bolt://localhost:7687"
    os.environ["NEO4J_USER"] = "neo4j"
    os.environ["NEO4J_PASSWORD"] = "password"
    asyncio.run(check_graph())
