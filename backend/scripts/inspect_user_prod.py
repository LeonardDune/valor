import os
from neo4j import GraphDatabase

# Production Credentials
URI = "neo4j+s://22317c1a.databases.neo4j.io"
AUTH = ("neo4j", "Y7O7YPMSGKuLzoQD6LGcll-I9kzSEmMZDbB5aTwAEWY")

def inspect_user_relations(tx, email):
    print(f"--- Inspecting User Relations for {email} ---")
    
    # Check User existence
    q_user = "MATCH (u:User {email: $email}) RETURN u.id as id, u.email as email"
    res = tx.run(q_user, email=email)
    user = res.single()
    
    if not user:
        print(f"User {email} NOT FOUND!")
        return

    print(f"User Found: {user['id']}")

    # Check relationships to ThemeBase
    q_rels = """
    MATCH (u:User {email: $email})-[r]->(tb:ThemeBase)
    RETURN type(r) as rel_type, tb.id as theme_id
    """
    res_rels = tx.run(q_rels, email=email)
    rels = list(res_rels)
    
    if not rels:
        print("No relationships found to any ThemeBase.")
    else:
        for r in rels:
            print(f" - [{r['rel_type']}] -> ThemeBase {r['theme_id']}")

    # Check relationships to Project/Organization for context
    q_context = """
    MATCH (u:User {email: $email})-[r]->(n)
    WHERE labels(n) in [['Project'], ['Organization']]
    RETURN type(r) as rel_type, labels(n) as labels, n.name as name
    """
    res_context = tx.run(q_context, email=email)
    for c in res_context:
        print(f" - [{c['rel_type']}] -> {c['labels'][0]} '{c['name']}'")

def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        session.execute_read(inspect_user_relations, "rl.wouters@hotmail.com") # Assuming email based on username 'rl.wouters' - wait, user said 'rl.wouters', usually that's ID or part of email.
        # Let's try matching on 'id' if email fails, or fuzzy match.
        # Better: Search by partial match if explicit email is unknown, but user said "name 'rl.wouters'". 
        # I'll try to find the user first.
        
    driver.close()

if __name__ == "__main__":
    main()
