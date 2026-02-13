import sys
import os
from neo4j import GraphDatabase

# Production Credentials
URI = "neo4j+s://22317c1a.databases.neo4j.io"
AUTH = ("neo4j", "Y7O7YPMSGKuLzoQD6LGcll-I9kzSEmMZDbB5aTwAEWY")

def inspect_db():
    print("Connecting to Production Database...")
    try:
        driver = GraphDatabase.driver(URI, auth=AUTH)
        driver.verify_connectivity()
        print("Connected successfully.\n")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    with driver.session() as session:
        # 1. Count Total Nodes
        count = session.run("MATCH (n) RETURN count(n) as total").single()["total"]
        print(f"Total Nodes: {count}")

        # 2. List Labels
        labels = session.run("CALL db.labels() YIELD label RETURN collect(label) as labels").single()["labels"]
        print(f"Labels: {labels}")

        # 3. List Relationship Types
        rels = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as rels").single()["rels"]
        print(f"Relationship Types: {rels}")
        print("-" * 40)

        # 4. Inspect Attributes of Key Nodes
        for label in ["Theme", "Factor", "Claim", "Project", "Organization"]:
            if label in labels:
                print(f"\nScanning {label} nodes...")
                # Get count
                c = session.run(f"MATCH (n:{label}) RETURN count(n) as c").single()["c"]
                print(f"  Count: {c}")
                
                # Get sample properties
                sample = session.run(f"MATCH (n:{label}) RETURN n LIMIT 1").single()
                if sample:
                    node = sample["n"]
                    print(f"  Sample Properties: {dict(node)}")
                    
                    # Check relationships
                    print("  Outgoing Relationships:")
                    rels_out = session.run(f"MATCH (n:{label})-[r]->(m) RETURN type(r) as t, labels(m) as l LIMIT 5")
                    for r in rels_out:
                         print(f"    -[:{r['t']}]->({r['l']})")
            else:
                print(f"\nLabel {label} NOT FOUND.")

        # 5. Check for Temporal Structure (Expect None)
        print("\nChecking for Temporal Structure...")
        temporal_labels = ["ThemeVersion", "ThemeBase", "FactorVersion", "ClaimVersion"]
        found_temporal = [l for l in temporal_labels if l in labels]
        if found_temporal:
            print(f"WARNING: Found temporal labels: {found_temporal}")
        else:
            print("Verified: No temporal labels found.")

    driver.close()

if __name__ == "__main__":
    inspect_db()
