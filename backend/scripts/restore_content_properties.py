import os
from neo4j import GraphDatabase

# Production Credentials
URI = "neo4j+s://22317c1a.databases.neo4j.io"
AUTH = ("neo4j", "Y7O7YPMSGKuLzoQD6LGcll-I9kzSEmMZDbB5aTwAEWY")

def restore_content_properties(tx):
    print("--- Restoring 'created_by' Property for Factors and Claims ---")
    
    # Query 1: Set created_by on FactorBase based on CREATED relationship (which we just fixed)
    q_factors = """
    MATCH (u:User)-[:CREATED]->(fb:FactorBase)
    WHERE fb.created_by IS NULL
    SET fb.created_by = u.id
    RETURN count(fb) as updated, u.email as owner
    """
    res_f = tx.run(q_factors)
    for rec in res_f:
        print(f"Updated {rec['updated']} FactorBase nodes for {rec['owner']}")
        
    # Query 2: Set created_by on ClaimBase
    q_claims = """
    MATCH (u:User)-[:CREATED]->(cb:ClaimBase)
    WHERE cb.created_by IS NULL
    SET cb.created_by = u.id
    RETURN count(cb) as updated, u.email as owner
    """
    res_c = tx.run(q_claims)
    for rec in res_c:
        print(f"Updated {rec['updated']} ClaimBase nodes for {rec['owner']}")

def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        session.execute_write(restore_content_properties)
    driver.close()

if __name__ == "__main__":
    main()
