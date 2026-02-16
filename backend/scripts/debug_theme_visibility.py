import os
from neo4j import GraphDatabase

# Production Credentials
URI = "neo4j+s://22317c1a.databases.neo4j.io"
AUTH = ("neo4j", "Y7O7YPMSGKuLzoQD6LGcll-I9kzSEmMZDbB5aTwAEWY")

def diagnose_visibility(tx, email):
    print(f"--- Diagnosing Visibility for {email} ---")
    
    # 1. Get User ID
    u = tx.run("MATCH (u:User {email: $email}) RETURN u.id as uid", email=email).single()
    if not u:
        print("User not found execution stopped.")
        return
    uid = u['uid']
    print(f"User ID: {uid}")

    # 2. Check strict dashboard query parts
    
    # A. User -> Theme (Direct or Indirect)
    q_access = """
    MATCH (u:User {id: $uid})
    MATCH (t:Theme)
    WHERE EXISTS((u)-[:HAS_ROLE]->(t)) 
       OR EXISTS((u)-[:HAS_ROLE]->(:Project)-[:HAS_THEME]->(t))
    RETURN t.id, t.name
    """
    res_access = tx.run(q_access, uid=uid)
    themes = list(res_access)
    print(f"Themes accessible via Role: {len(themes)}")
    for t in themes:
        print(f"  - Theme: {t['t.id']}")

        # B. Check Project and Org Connection for this Theme
        q_chain = """
        MATCH (t:Theme {id: $tid})
        OPTIONAL MATCH (p:Project)-[:HAS_THEME]->(t)
        OPTIONAL MATCH (o:Organization)-[:OWNS]->(p)
        RETURN p.name as proj, o.name as org, p.id as pid, o.id as oid
        """
        chain = tx.run(q_chain, tid=t['t.id']).single()
        if chain:
            print(f"    -> Project: {chain['proj']} ({chain['pid']})")
            if chain['org']:
                print(f"    -> Organization: {chain['org']} ({chain['oid']})")
            else:
                print(f"    -> [CRITICAL] Organization MISSING (Project is orphan)")
        else:
             print(f"    -> [CRITICAL] Project MISSING")

        # C. Check Active Version
        q_ver = """
        MATCH (t:Theme {id: $tid})
        OPTIONAL MATCH (t)-[:HAS_ACTIVE_VERSION]->(tv:ThemeVersion)
        RETURN tv.id as vid, tv.name as vname, tv.status as status
        """
        ver = tx.run(q_ver, tid=t['t.id']).single()
        if ver and ver['vid']:
             print(f"    -> Active Version: {ver['vname']} ({ver['status']})")
        else:
             print(f"    -> [CRITICAL] Active Version MISSING or linkage broken")

def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        session.execute_read(diagnose_visibility, "rl.wouters@gmail.com")
    driver.close()

if __name__ == "__main__":
    main()
