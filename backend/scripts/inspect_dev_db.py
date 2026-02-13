import sys
import os
from neo4j import GraphDatabase

# DEV Credentials (from .env)
URI = "neo4j+s://7fe30728.databases.neo4j.io"
AUTH = ("neo4j", "YjwfR8H_Oma0RiEI7pI8JAOTF2EBHMj6qXoOD4VTgQM")

def inspect_db():
    print("Connecting to Development Database...")
    try:
        driver = GraphDatabase.driver(URI, auth=AUTH)
        driver.verify_connectivity()
        print("Connected successfully.\n")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    with driver.session() as session:
        # 1. Structure Check
        print("--- Node Labels ---")
        labels = session.run("CALL db.labels() YIELD label RETURN collect(label) as labels").single()["labels"]
        print(f"Labels: {labels}")

        print("\n--- Relationship Types ---")
        rels = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as rels").single()["rels"]
        print(f"Relationship Types: {rels}")

        # 2. Verify Specific Temporal Patterns
        print("\n--- Checking Temporal Patterns ---")
        patterns = [
            "(:ThemeBase)-[:HAS_VERSION]->(:ThemeVersion)",
            "(:ThemeBase)-[:HAS_ACTIVE_VERSION]->(:ThemeVersion)",
            "(:ThemeVersion)-[:HAS_FACTOR]->(:FactorVersion)",
            "(:FactorBase)-[:HAS_VERSION]->(:FactorVersion)",
            "(:ThemeVersion)-[:IN_SCOPE]->(:FactorBase)",
            "(:ThemeVersion)-[:HAS_CLAIM]->(:ClaimVersion)",
            "(:ClaimBase)-[:HAS_VERSION]->(:ClaimVersion)",
            "(:ThemeVersion)-[:IN_SCOPE]->(:ClaimBase)",
            "(:FactorVersion)-[:CLAIMS]->(:ClaimVersion)",
            "(:ClaimVersion)-[:TO]->(:FactorVersion)"
        ]
        
        for p in patterns:
            res = session.run(f"MATCH {p} RETURN count(*) as c LIMIT 1").single()
            count = res["c"] if res else 0
            start = p.split("-")[0]
            rel = p.split("-")[1]
            end = p.split("->")[1]
            print(f"Pattern {start}-{rel}->{end}: {'✅ FOUND' if count > 0 else '❌ NOT FOUND'}")

    driver.close()

if __name__ == "__main__":
    inspect_db()
