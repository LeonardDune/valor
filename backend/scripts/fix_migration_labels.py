import os
import sys
from neo4j import GraphDatabase

# Production Credentials
URI = "neo4j+s://22317c1a.databases.neo4j.io"
AUTH = ("neo4j", "Y7O7YPMSGKuLzoQD6LGcll-I9kzSEmMZDbB5aTwAEWY")

def fix_labels(tx):
    print("--- Removing Legacy Labels from Base Nodes ---")
    
    # 1. Remove 'Theme' from ThemeBase nodes
    q_theme = """
    MATCH (n:ThemeBase)
    REMOVE n:Theme
    RETURN count(n) as c
    """
    res = tx.run(q_theme)
    count = res.single()['c']
    print(f"Removed 'Theme' label from {count} ThemeBase nodes.")

    # 2. Remove 'Factor' from FactorBase nodes
    q_factor = """
    MATCH (n:FactorBase)
    REMOVE n:Factor
    RETURN count(n) as c
    """
    res = tx.run(q_factor)
    count = res.single()['c']
    print(f"Removed 'Factor' label from {count} FactorBase nodes.")

    # 3. Remove 'Claim' from ClaimBase nodes
    q_claim = """
    MATCH (n:ClaimBase)
    REMOVE n:Claim
    RETURN count(n) as c
    """
    res = tx.run(q_claim)
    count = res.single()['c']
    print(f"Removed 'Claim' label from {count} ClaimBase nodes.")

def main():
    print("Connecting to database to fix labels...")
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        session.execute_write(fix_labels)
    driver.close()
    print("Fix completed.")

if __name__ == "__main__":
    main()
