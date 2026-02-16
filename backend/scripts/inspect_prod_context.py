import os
from neo4j import GraphDatabase

# Production Credentials
URI = "neo4j+s://22317c1a.databases.neo4j.io"
AUTH = ("neo4j", "Y7O7YPMSGKuLzoQD6LGcll-I9kzSEmMZDbB5aTwAEWY")

def inspect_context(tx):
    print("--- Inspecting ANY relationships for rl.wouters ---")
    emails = ["rl.wouters@gmail.com", "rl.wouters@pm.me"]
    
    for email in emails:
        print(f"\nUser: {email}")
        q_any = """
        MATCH (u:User {email: $email})-[r]-(n)
        RETURN type(r) as rel, labels(n) as node_labels, n.name as node_name, n.id as node_id, startNode(r) = u as is_outgoing
        """
        res = tx.run(q_any, email=email)
        path_found = False
        for record in res:
            path_found = True
            direction = "->" if record['is_outgoing'] else "<-"
            print(f"  -[{record['rel']}]-{direction} ({record['node_labels'][0]}: {record['node_name']})")
        
        if not path_found:
            print("  (孤) No relationships found.")

    print("\n--- Inspecting Projects and their Users ---")
    q_projects = """
    MATCH (p:Project)
    OPTIONAL MATCH (u:User)-[r]->(p)
    RETURN p.name as proj_name, p.id as proj_id, u.email as user_email, type(r) as rel
    """
    res_proj = tx.run(q_projects)
    for p in res_proj:
        user_info = f"{p['user_email']} ({p['rel']})" if p['user_email'] else "No User Linked"
        print(f"Project: '{p['proj_name']}' ({p['proj_id']}) <- {user_info}")

def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        session.execute_read(inspect_context)
    driver.close()

if __name__ == "__main__":
    main()
