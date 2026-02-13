import os
from neo4j import GraphDatabase

# Production Credentials
URI = "neo4j+s://22317c1a.databases.neo4j.io"
AUTH = ("neo4j", "Y7O7YPMSGKuLzoQD6LGcll-I9kzSEmMZDbB5aTwAEWY")

def restore_user_relations(tx, email, project_name):
    print(f"--- Restoring Relations for {email} to Theme in '{project_name}' ---")
    
    # 1. Find User
    q_user = "MATCH (u:User {email: $email}) RETURN u.id as uid"
    user = tx.run(q_user, email=email).single()
    if not user:
        print(f"User {email} not found.")
        return
    uid = user['uid']
    
    # 2. Find Project and its ThemeBase
    q_theme = """
    MATCH (p:Project {name: $pname})-[:HAS_THEME]->(tb:ThemeBase)
    RETURN p.id as pid, tb.id as tid
    """
    record = tx.run(q_theme, pname=project_name).single()
    
    if not record:
        print(f"Project '{project_name}' or its ThemeBase not found.")
        return
        
    tid = record['tid']
    print(f"Found ThemeBase: {tid}")
    
    # 3. Create Relationships
    q_create = """
    MATCH (u:User {id: $uid})
    MATCH (tb:ThemeBase {id: $tid})
    
    MERGE (u)-[r1:HAS_ROLE]->(tb)
    ON CREATE SET r1.role = 'admin'
    ON MATCH SET r1.role = 'admin'
    
    MERGE (u)-[r2:CREATED]->(tb)
    ON CREATE SET r2.created_at = datetime()
    
    RETURN type(r1), type(r2)
    """
    tx.run(q_create, uid=uid, tid=tid)
    print(f"Restored HAS_ROLE 'admin' and CREATED for {email} -> ThemeBase {tid}")

def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        # Hardcoded based on inspection findings
        session.execute_write(restore_user_relations, "rl.wouters@gmail.com", "ZSM-Jeugd in Noord-Holland")
        
    driver.close()

if __name__ == "__main__":
    main()
