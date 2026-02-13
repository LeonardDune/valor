import os
import sys
from neo4j import GraphDatabase

# Production Credentials
URI = "neo4j+s://22317c1a.databases.neo4j.io"
AUTH = ("neo4j", "Y7O7YPMSGKuLzoQD6LGcll-I9kzSEmMZDbB5aTwAEWY")

def restore_theme_factor_relations(tx):
    print("--- Restoring ThemeBase -> FactorBase Relationships (Graph Traversal) ---")
    
    # Logic V3: Graph Traversal
    # Explicitly use the relationships we know exist:
    # (tb)-[HAS_ACTIVE_VERSION]->(tv)-[HAS_FACTOR]->(fv)<-[HAS_VERSION]-(fb)
    # Then create (tb)-[:HAS_FACTOR]->(fb)
    
    q_restore = """
    MATCH (tb:ThemeBase)-[:HAS_ACTIVE_VERSION]->(tv:ThemeVersion)
    MATCH (tv)-[:HAS_FACTOR]->(fv:FactorVersion)
    MATCH (fb:FactorBase)-[:HAS_VERSION]->(fv)
    
    MERGE (tb)-[:HAS_FACTOR]->(fb)
    
    RETURN count(fb) as restored_count
    """
    
    res = tx.run(q_restore)
    record = res.single()
    print(f"Restored/Verified {record['restored_count']} ThemeBase->FactorBase relationships.")

def main():
    print("Connecting to database...")
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        session.execute_write(restore_theme_factor_relations)
    driver.close()
    print("Done.")

if __name__ == "__main__":
    main()
