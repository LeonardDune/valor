import asyncio
import os
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

async def verify_spaces():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    query_spaces = """
    MATCH (s:Space)
    OPTIONAL MATCH (s)<-[:HAS_SPACE]-(t:Theme)
    RETURN s.id as id, s.name as name, t.name as theme, t.id as theme_id
    """
    
    query_relationships = """
    MATCH (u:User)-[r:HAS_ROLE]->(s:Space)
    RETURN u.email as email, r.role as role, s.name as space_name
    """
    
    try:
        with driver.session() as session:
            print("--- EXISTING SPACES ---")
            spaces = session.run(query_spaces).data()
            if not spaces:
                print("No spaces found in database.")
            for space in spaces:
                print(f"Space: {space['name']} (ID: {space['id']}) - Theme: {space['theme']} (ID: {space['theme_id']})")

            print("\n--- SPACE MEMBERSHIPS (Explicit) ---")
            rels = session.run(query_relationships).data()
            if not rels:
                print("No user-space relationships found.")
            for rel in rels:
                print(f"User: {rel['email']} -> Role: {rel['role']} -> Space: {rel['space_name']}")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    asyncio.run(verify_spaces())
