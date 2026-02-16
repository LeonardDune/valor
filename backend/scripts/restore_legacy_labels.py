import os
from neo4j import GraphDatabase

# Production Credentials
URI = "neo4j+s://22317c1a.databases.neo4j.io"
AUTH = ("neo4j", "Y7O7YPMSGKuLzoQD6LGcll-I9kzSEmMZDbB5aTwAEWY")

def restore_legacy_labels(tx):
    print("--- Restoring Legacy Labels for Compatibility ---")
    
    # ThemeBase -> Theme
    q_theme = """
    MATCH (n:ThemeBase)
    SET n:Theme
    RETURN count(n) as count
    """
    res_t = tx.run(q_theme).single()
    print(f"Added :Theme label to {res_t['count']} ThemeBase nodes.")
    
    # FactorBase -> Factor
    q_factor = """
    MATCH (n:FactorBase)
    SET n:Factor
    RETURN count(n) as count
    """
    res_f = tx.run(q_factor).single()
    print(f"Added :Factor label to {res_f['count']} FactorBase nodes.")
    
    # ClaimBase -> Claim
    # Note: Ensure we don't accidentally label ClaimVersions if they have Base label (unlikely but safe to check)
    q_claim = """
    MATCH (n:ClaimBase)
    SET n:Claim
    RETURN count(n) as count
    """
    res_c = tx.run(q_claim).single()
    print(f"Added :Claim label to {res_c['count']} ClaimBase nodes.")

def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        session.execute_write(restore_legacy_labels)
    driver.close()

if __name__ == "__main__":
    main()
