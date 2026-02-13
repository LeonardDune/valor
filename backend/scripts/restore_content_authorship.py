import os
from neo4j import GraphDatabase

# Production Credentials
URI = "neo4j+s://22317c1a.databases.neo4j.io"
AUTH = ("neo4j", "Y7O7YPMSGKuLzoQD6LGcll-I9kzSEmMZDbB5aTwAEWY")

def restore_content_authorship(tx):
    print("--- Restoring Authorship for Factors and Claims ---")
    
    # Strategy:
    # 1. Match ThemeBase and its 'Owner' (User with HAS_ROLE='admin' or CREATED)
    # 2. Find all FactorBase and ClaimBase nodes connected to that Theme
    # 3. Create [:CREATED] relationship from User to those Base nodes
    
    # Query 1: Link FactorBase to Theme Owner
    q_factors = """
    MATCH (u:User)-[:HAS_ROLE {role: 'admin'}]->(tb:ThemeBase)
    MATCH (tb)-[:HAS_FACTOR]->(fb:FactorBase)
    
    MERGE (u)-[r:CREATED]->(fb)
    ON CREATE SET r.created_at = datetime()
    
    RETURN count(fb) as factors_linked, u.email as owner
    """
    res_f = tx.run(q_factors)
    for rec in res_f:
        print(f"Linked {rec['factors_linked']} FactorBase nodes to {rec['owner']}")
        
    # Query 2: Link ClaimBase to Theme Owner
    # Path: ThemeBase -> ThemeVersion -> HAS_CLAIM -> ClaimVersion -> base_id -> ClaimBase
    # OR:   ThemeBase -> ThemeVersion -> HAS_FACTOR -> FactorVersion ... Claim ... (Legacy path is gone)
    # Let's use the new structure: TV -> HAS_CLAIM -> CV -> base -> CB
    q_claims = """
    MATCH (u:User)-[:HAS_ROLE {role: 'admin'}]->(tb:ThemeBase)
    MATCH (tb)-[:HAS_ACTIVE_VERSION]->(tv:ThemeVersion)
    MATCH (tv)-[:HAS_CLAIM]->(cv:ClaimVersion)
    MATCH (cb:ClaimBase {id: cv.base_id})
    
    MERGE (u)-[r:CREATED]->(cb)
    ON CREATE SET r.created_at = datetime()
    
    RETURN count(cb) as claims_linked, u.email as owner
    """
    res_c = tx.run(q_claims)
    for rec in res_c:
        print(f"Linked {rec['claims_linked']} ClaimBase nodes to {rec['owner']}")

    # Fallback: If Theme has CREATED but not HAS_ROLE (though I added both for rl.wouters)
    # But let's stick to HAS_ROLE 'admin' as the strong ownership signal.

def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        session.execute_write(restore_content_authorship)
    driver.close()

if __name__ == "__main__":
    main()
