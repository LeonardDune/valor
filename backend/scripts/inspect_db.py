import os
import sys

# Add backend directory to sys.path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.utils import get_driver

def inspect_db():
    driver = get_driver()
    with driver.session() as session:
        print("--- USERS ---")
        users = session.run("MATCH (u:User) RETURN u.id, u.name, u.email, u.role").data()
        for u in users:
            print(f"User: {u['u.name']} ({u['u.role']}) - ID: {u['u.id']} - Email: {u.get('u.email', 'N/A')}")
        
        print("\n--- THEMES ---")
        themes = session.run("MATCH (t:Theme) RETURN t.id, t.name").data()
        for t in themes:
            print(f"Theme: {t['t.name']} ({t['t.id']})")
            # Count factors
            count = session.run("MATCH (t:Theme {id: $tid})-[:HAS_FACTOR]->(f) RETURN count(f) as c", tid=t['t.id']).single()['c']
            print(f"  -> Has {count} Factors")

        print("\n--- NODES SUMMARY ---")
        summary = session.run("MATCH (n) RETURN labels(n) as l, count(n) as c").data()
        for s in summary:
            print(f"{s['l']}: {s['c']}")

    driver.close()

if __name__ == "__main__":
    inspect_db()
