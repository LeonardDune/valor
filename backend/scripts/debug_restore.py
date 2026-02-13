import os
import sys
from neo4j import GraphDatabase

# Production Credentials
URI = "neo4j+s://22317c1a.databases.neo4j.io"
AUTH = ("neo4j", "Y7O7YPMSGKuLzoQD6LGcll-I9kzSEmMZDbB5aTwAEWY")

def inspect_ids(tx):
    print("--- Inspecting IDs for debugging ---")
    
    # Check a sample ThemeVersion and its FactorVersions
    q_inspect = """
    MATCH (tv:ThemeVersion)-[:HAS_FACTOR]->(fv:FactorVersion)
    RETURN tv.id as tv_id, tv.base_id as tv_base_id, fv.id as fv_id, fv.base_id as fv_base_id LIMIT 5
    """
    res = tx.run(q_inspect)
    for record in res:
        print(f"TV: {record['tv_id']} (Base: {record['tv_base_id']}) -> FV: {record['fv_id']} (Base: {record['fv_base_id']})")
        
        # Check if the Base nodes exist with these IDs
        tv_base_id = record['tv_base_id']
        fv_base_id = record['fv_base_id']
        
        # Check ThemeBase
        res_tb = tx.run("MATCH (tb:ThemeBase {id: $id}) RETURN count(tb) as c", {"id": tv_base_id})
        updated = res_tb.single()['c']
        print(f"  -> ThemeBase {tv_base_id} exists? {updated > 0}")
        
        # Check FactorBase
        res_fb = tx.run("MATCH (fb:FactorBase {id: $id}) RETURN count(fb) as c", {"id": fv_base_id})
        updated_f = res_fb.single()['c']
        print(f"  -> FactorBase {fv_base_id} exists? {updated_f > 0}")

def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        session.execute_read(inspect_ids)
    driver.close()

if __name__ == "__main__":
    main()
