import os
import sys
from neo4j import GraphDatabase

# Production Credentials
URI = "neo4j+s://22317c1a.databases.neo4j.io"
AUTH = ("neo4j", "Y7O7YPMSGKuLzoQD6LGcll-I9kzSEmMZDbB5aTwAEWY")

def delete_legacy_threads(tx):
    print("--- Deleting Legacy ConversationThreads linked to ThemeBase ---")
    
    # Match threads linked to ThemeBase (Legacy)
    # Also optionally match messages belonging to these threads to clean them up too.
    q_delete = """
    MATCH (ct:ConversationThread)-[:HAS_THEME|BELONGS_TO]->(tb:ThemeBase)
    OPTIONAL MATCH (m:ConversationMessage)-[:BELONGS_TO]->(ct)
    
    WITH ct, m
    DETACH DELETE ct, m
    
    RETURN count(ct) as deleted_threads, count(m) as deleted_messages
    """
    
    res = tx.run(q_delete)
    record = res.single()
    print(f"Deleted {record['deleted_threads']} threads.")
    print(f"Deleted {record['deleted_messages']} messages.")

def main():
    print("Connecting to database to delete legacy threads...")
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        session.execute_write(delete_legacy_threads)
    driver.close()
    print("Deletion completed.")

if __name__ == "__main__":
    main()
