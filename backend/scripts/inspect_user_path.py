import os
from neo4j import GraphDatabase

# Production Credentials
URI = "neo4j+s://22317c1a.databases.neo4j.io"
AUTH = ("neo4j", "Y7O7YPMSGKuLzoQD6LGcll-I9kzSEmMZDbB5aTwAEWY")

def inspect_user_path(tx, email):
    print(f"--- Inspecting Path for {email} ---")
    
    # 1. User -> Project
    q_proj = """
    MATCH (u:User {email: $email})-[r]->(p:Project)
    RETURN u.id as uid, type(r) as rel, p.id as pid, p.name as pname
    """
    res_proj = tx.run(q_proj, email=email)
    projects = list(res_proj)
    
    if not projects:
        print("User has no direct relationship to any Project.")
    
    for p in projects:
        print(f"User -[{p['rel']}]-> Project '{p['pname']}' ({p['pid']})")
        
        # 2. Project -> Theme (Base)
        q_theme = """
        MATCH (p:Project {id: $pid})-[:HAS_THEME]->(tb:ThemeBase)
        RETURN tb.id as tid
        """
        res_theme = tx.run(q_theme, pid=p['pid'])
        themes = list(res_theme)
        
        for t in themes:
            print(f"  Project -> HAS_THEME -> ThemeBase ({t['tid']})")
            
            # 3. Check specific User -> ThemeBase relation
            q_check = """
            MATCH (u:User {email: $email})-[r]->(tb:ThemeBase {id: $tid})
            RETURN type(r) as rel
            """
            res_check = tx.run(q_check, email=email, tid=t['tid'])
            rels = [r['rel'] for r in res_check]
            print(f"  Direct User->ThemeBase Rels: {rels}")

def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        session.execute_read(inspect_user_path, "rl.wouters@gmail.com")
        session.execute_read(inspect_user_path, "rl.wouters@pm.me") # Check the other one too just in case

    driver.close()

if __name__ == "__main__":
    main()
