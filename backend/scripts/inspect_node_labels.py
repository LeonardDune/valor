import os
from neo4j import GraphDatabase

# Production Credentials
URI = "neo4j+s://22317c1a.databases.neo4j.io"
AUTH = ("neo4j", "Y7O7YPMSGKuLzoQD6LGcll-I9kzSEmMZDbB5aTwAEWY")

def inspect_labels(tx, email):
    print(f"--- Inspecting Labels for Themes connected to {email} ---")
    
    # query specifically for ThemeBase to see what labels it has
    q = """
    MATCH (u:User {email: $email})
    MATCH (u)-[:HAS_ROLE]->(target)
    RETURN labels(target) as lbls, target.id as tid
    """
    res = tx.run(q, email=email)
    found = False
    for rec in res:
        found = True
        print(f"Node {rec['tid']} has labels: {rec['lbls']}")
        if "Theme" not in rec['lbls'] and "ThemeBase" in rec['lbls']:
             print("  [CRITICAL] Node is ThemeBase but NOT Theme. Dashboard query will fail.")

    if not found:
        print("No HAS_ROLE relationships found for user.")

def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        session.execute_read(inspect_labels, "rl.wouters@gmail.com")
    driver.close()

if __name__ == "__main__":
    main()
