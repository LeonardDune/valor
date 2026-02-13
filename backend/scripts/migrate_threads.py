import os
import sys
from neo4j import GraphDatabase

# Production Credentials
URI = "neo4j+s://22317c1a.databases.neo4j.io"
AUTH = ("neo4j", "Y7O7YPMSGKuLzoQD6LGcll-I9kzSEmMZDbB5aTwAEWY")

def migrate_threads(tx):
    print("--- Migrating ConversationThreads from ThemeBase to ThemeVersion ---")
    
    # Strategy:
    # 1. Find Threads linked to ThemeBase via HAS_THEME or HAS_THREAD (Legacy seems to be HAS_THEME incoming?)
    #    Inspection said: (t:ThemeBase)<-[:HAS_THEME]-(ct:ConversationThread)
    #    OR (t:ThemeBase)-[:HAS_THREAD]->(ct:ConversationThread) ??
    #    Let's check both directions to be safe, or rely on inspection.
    #    Inspection: -[:BELONGS_TO]->(['ThemeBase']): 155. Wait, inspection output said `BELONGS_TO`!
    #    Wait, my inspect_threads script query was: `MATCH (t:ThemeBase)<-[:HAS_THEME]-(ct:ConversationThread)`
    #    But the output said: `-[:BELONGS_TO]->(['ThemeBase']): 155`
    #    Let's check the inspect_threads.py code again to be sure what I queried vs what I printed.
    
    #    Query was: MATCH (t:ThemeBase)<-[:HAS_THEME]-(ct:ConversationThread)
    #    If that returned 155, then the relationship is HAS_THEME.
    #    But the 'Outgoing Relations' part printed BELONGS_TO.
    #    Maybe both exist? Or I misread the output.
    #    Let's handle the specific relation found: HAS_THEME (incoming to Theme) or BELONGS_TO.
    
    #    Let's look at inspect_prod_db.py output from Step 7937: Relationship Types: [..., 'BELONGS_TO', 'HAS_THEME', ...]
    
    #    I will match (ct)-[r]->(tb:ThemeBase).
    
    q_migrate = """
    MATCH (ct:ConversationThread)-[r]->(tb:ThemeBase)
    MATCH (tb)-[:HAS_ACTIVE_VERSION]->(tv:ThemeVersion)
    
    // Create new relationship to Version
    CREATE (ct)-[:BELONGS_TO]->(tv) 
    // Note: Verify if 'BELONGS_TO' or 'HAS_THREAD' is the standard.
    // Domain/CRUD uses:
    // create_thread: MATCH (s) ... CREATE (s)-[:HAS_THREAD]->(t)
    // get_threads: MATCH (s)-[:HAS_THREAD]->(t)
    // So the NEW standard is (Parent)-[:HAS_THREAD]->(Child).
    
    // The OLD standard seems to be (Child)-[:HAS_THEME|BELONGS_TO]->(Parent).
    
    // ACTION:
    // 1. Delete old relationship 'r'
    // 2. Create new relationship (tv)-[:HAS_THREAD]->(ct)
    
    DELETE r
    CREATE (tv)-[:HAS_THREAD]->(ct)
    
    RETURN count(ct) as migrated_count
    """
    
    res = tx.run(q_migrate)
    count = res.single()['migrated_count']
    print(f"Migrated {count} threads to Active Theme Versions.")

def main():
    print("Migrating Threads...")
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        session.execute_write(migrate_threads)
    driver.close()
    print("Done.")

if __name__ == "__main__":
    main()
