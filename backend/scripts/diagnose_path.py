import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.utils import get_driver

def diagnose():
    driver = get_driver()
    user_email = "rl.wouters@gmail.com"
    
    print(f"🕵️ Diagnosing Access Path for {user_email}...")
    
    with driver.session() as session:
        # 1. Check User
        u = session.run("MATCH (u:User {email: $email}) RETURN u.id, u.name", {"email": user_email}).single()
        if not u:
            print("❌ User NOT FOUND!")
            return
        print(f"✅ User Found: {u['u.id']} ({u['u.name']})")
        uid = u['u.id']

        # 2. Check Org Membership
        orgs = session.run("""
        MATCH (u:User {id: $uid})-[r:HAS_ROLE]->(o:Organization)
        RETURN o.id, o.name, r.role
        """, {"uid": uid}).data()
        
        if not orgs:
            print("❌ No Organization Membership found!")
        else:
            print(f"✅ User is member of {len(orgs)} Orgs:")
            for o in orgs:
                print(f"   - Org: {o['o.name']} ({o['o.id']}) | Role: {o['r.role']}")
                
                # 3. Check Projects in Org
                projs = session.run("""
                MATCH (o:Organization {id: $oid})-[:OWNS]->(p:Project)
                OPTIONAL MATCH (u:User {id: $uid})-[r:HAS_ROLE]->(p)
                RETURN p.id, p.name, r.role
                """, {"oid": o['o.id'], "uid": uid}).data()
                
                if not projs:
                    print(f"     ⚠️ No Projects in Org {o['o.name']}")
                else:
                    for p in projs:
                        print(f"     - Project: {p['p.name']} ({p['p.id']}) | Direct Role: {p['r.role']}")
                        
                        # 4. Check Themes in Project
                        themes = session.run("""
                        MATCH (p:Project {id: $pid})-[:HAS_THEME]->(t:Theme)
                        OPTIONAL MATCH (u:User {id: $uid})-[r:HAS_ROLE]->(t)
                        RETURN t.id, t.name, r.role
                        """, {"pid": p['p.id'], "uid": uid}).data()
                        
                        if not themes:
                            print(f"       ⚠️ No Themes in Project {p['p.name']}")
                        else:
                            for t in themes:
                                print(f"       - Theme: {t['t.name']} ({t['t.id']}) | Direct Role: {t['r.role']}")
                                
                                # 5. Check Versions
                                vers = session.run("""
                                MATCH (t:Theme {id: $tid})-[:HAS_VERSION]->(v:ThemeVersion)
                                RETURN count(v) as c
                                """, {"tid": t['t.id']}).single()
                                print(f"         Versions count: {vers['c']}")

if __name__ == "__main__":
    diagnose()
