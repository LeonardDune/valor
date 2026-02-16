import os
from neo4j import GraphDatabase

# Production Credentials
URI = "neo4j+s://22317c1a.databases.neo4j.io"
AUTH = ("neo4j", "Y7O7YPMSGKuLzoQD6LGcll-I9kzSEmMZDbB5aTwAEWY")

def inspect_created_rels(tx):
    print("--- Inspecting CREATED relationships on Base nodes ---")
    
    # Check FactorBase
    q_fb = """
    MATCH (fb:FactorBase)
    OPTIONAL MATCH (u:User)-[r:CREATED]->(fb)
    RETURN count(fb) as total, count(r) as with_user, labels(fb) as tags
    """
    res_fb = tx.run(q_fb).single()
    print(f"FactorBase: Total {res_fb['total']}, With User Link: {res_fb['with_user']}")
    
    # Check ClaimBase
    q_cb = """
    MATCH (cb:ClaimBase)
    OPTIONAL MATCH (u:User)-[r:CREATED]->(cb)
    RETURN count(cb) as total, count(r) as with_user
    """
    res_cb = tx.run(q_cb).single()
    print(f"ClaimBase: Total {res_cb['total']}, With User Link: {res_cb['with_user']}")
    
    # Check if they have 'created_by' property
    q_props = """
    MATCH (n) WHERE n:FactorBase OR n:ClaimBase
    RETURN labels(n) as lbl, count(n) as total, count(n.created_by) as has_prop
    """
    res_props = tx.run(q_props)
    for r in res_props:
        print(f"{r['lbl']}: Total {r['total']}, Has 'created_by' prop: {r['has_prop']}")

def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        session.execute_read(inspect_created_rels)
    driver.close()

if __name__ == "__main__":
    main()
