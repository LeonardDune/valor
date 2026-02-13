import os
import sys
from neo4j import GraphDatabase

# Production Credentials
URI = "neo4j+s://22317c1a.databases.neo4j.io"
AUTH = ("neo4j", "Y7O7YPMSGKuLzoQD6LGcll-I9kzSEmMZDbB5aTwAEWY")

def inspect_threads(tx):
    print("--- Inspecting ConversationThread nodes linked to ThemeBase ---")
    
    # Count threads linked to ThemeBase
    q_count = """
    MATCH (t:ThemeBase)<-[:HAS_THEME]-(ct:ConversationThread)
    RETURN count(ct) as count, t.name as theme_name
    """
    res = tx.run(q_count)
    print("Counts per Theme:")
    for record in res:
        print(f"  Theme: {record['theme_name']} - Threads: {record['count']}")

    # Inspect a few sample threads
    q_sample = """
    MATCH (t:ThemeBase)<-[:HAS_THEME]-(ct:ConversationThread)
    RETURN ct, t.name as theme_name LIMIT 5
    """
    res = tx.run(q_sample)
    print("\nSample Threads:")
    for record in res:
        ct = record['ct']
        print(f"  Thread ID: {ct.get('id')}")
        print(f"  Theme: {record['theme_name']}")
        print(f"  Props: {dict(ct)}")
        print("---")

    # Check if they have messages or other relations
    q_relations = """
    MATCH (ct:ConversationThread)-[r]->(n)
    RETURN type(r) as rel_type, labels(n) as target_labels, count(*) as count
    """
    res = tx.run(q_relations)
    print("\nOutgoing Relations from Threads:")
    for record in res:
        print(f"  -[:{record['rel_type']}]->({record['target_labels']}): {record['count']}")

def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        session.execute_read(inspect_threads)
    driver.close()

if __name__ == "__main__":
    main()
