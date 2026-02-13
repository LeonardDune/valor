import os
import sys
import uuid
from neo4j import GraphDatabase

# Production Credentials (load from env or hardcode for this one-off script)
URI = "neo4j+s://22317c1a.databases.neo4j.io"
AUTH = ("neo4j", "Y7O7YPMSGKuLzoQD6LGcll-I9kzSEmMZDbB5aTwAEWY")

DRY_RUN = True

def run_query(tx, query, params=None):
    if DRY_RUN:
        print(f"[DRY RUN] Would execute:\n{query}\nParams: {params}\n")
        return []
    else:
        result = tx.run(query, params)
        return [record.data() for record in result]

def migrate_themes(tx):
    print("\n--- Migrating Themes ---")
    # 1. Select legacy Themes that haven't been migrated yet (check for ThemeBase label)
    q_fetch = "MATCH (t:Theme) WHERE NOT t:ThemeBase RETURN t"
    res = tx.run(q_fetch) # Always run fetch
    
    themes = [r["t"] for r in res]
    print(f"Found {len(themes)} legacy themes to migrate.")
    
    for t in themes:
        t_props = dict(t)
        tid = t_props["id"]
        v_id = str(uuid.uuid4())
        
        print(f"Migrating Theme: {t_props.get('name')} ({tid}) -> Version {v_id}")
        
        # 1. Label as ThemeBase
        # 2. Create ThemeVersion
        # 3. Link
        
        q_migrate = """
        MATCH (t:Theme {id: $tid})
        SET t:ThemeBase
        
        CREATE (tv:ThemeVersion {
            id: $vid,
            version_number: 1,
            name: t.name,
            description: t.description,
            status: t.status,
            created_at: datetime()
        })
        
        CREATE (t)-[:HAS_VERSION]->(tv)
        CREATE (t)-[:HAS_ACTIVE_VERSION]->(tv)
        
        // Return IDs for next steps
        RETURN t.id as base_id, tv.id as version_id
        """
        run_query(tx, q_migrate, {"tid": tid, "vid": v_id})
        
        # Migrate Factors for this Theme
        migrate_factors(tx, tid, v_id)

def migrate_factors(tx, theme_base_id, theme_version_id):
    print(f"  Migrating Factors for Theme {theme_base_id}...")
    
    # Fetch Factors linked to this Theme (assuming legacy relation uses HAS_FACTOR)
    q_fetch = """
    MATCH (t:Theme {id: $tid})-[:HAS_FACTOR]->(f:Factor)
    RETURN f
    """
    res = tx.run(q_fetch, {"tid": theme_base_id})
    factors = [r["f"] for r in res]
    print(f"  Found {len(factors)} factors.")
    
    for f in factors:
        f_props = dict(f)
        fid = f_props["id"]
        fv_id = str(uuid.uuid4())
        
        q_factors = """
        MATCH (f:Factor {id: $fid})
        MATCH (tv:ThemeVersion {id: $tvid})
        SET f:FactorBase
        
        CREATE (fv:FactorVersion {
            id: $fvid,
            base_id: f.id,
            name: f.name,
            description: f.description,
            type: coalesce(f.type, 'systeemelement'),
            sources: [],
            created_at: datetime()
        })
        
        CREATE (tv)-[:HAS_FACTOR]->(fv)
        CREATE (f)-[:HAS_VERSION]->(fv)
        """
        run_query(tx, q_factors, {"fid": fid, "fvid": fv_id, "tvid": theme_version_id})

    # Migrate Claims (Needs Factors to be ready)
    migrate_claims(tx, theme_version_id)

def migrate_claims(tx, theme_version_id):
    print(f"  Migrating Claims within Version {theme_version_id}...")
    
    # We need to find claims that connect factors WHICH ARE now in this version
    # Legacy: (Factor)-[:CLAIMS]->(Claim)-[:TO]->(Factor)
    # New: (fv1)-[:CLAIMS]->(cv)-[:TO]->(fv2)
    
    # Strategy: Find legacy structures involving factors in this theme
    # Note: In legacy, Factors might be shared or specific. Assuming specific per theme for now based on 'HAS_FACTOR'.
    
    q_migrate_claims = """
    MATCH (tv:ThemeVersion {id: $tvid})-[:HAS_FACTOR]->(fv_source:FactorVersion)
    MATCH (source_base:FactorBase {id: fv_source.base_id})
    
    // Find legacy claim path from the source factor
    MATCH (source_base)-[rel_c:CLAIMS]->(c:Claim)-[rel_t:TO]->(target_base:Factor)
    
    // Ensure target is also in this version (to be safe)
    MATCH (tv)-[:HAS_FACTOR]->(fv_target:FactorVersion {base_id: target_base.id})
    
    // Check if duplicate processing (if ClaimBase already exists)
    WHERE NOT c:ClaimBase
    
    WITH tv, fv_source, c, rel_c, rel_t, fv_target
    
    SET c:ClaimBase
    
    CREATE (cv:ClaimVersion {
        id: randomUUID(),
        base_id: c.id,
        statement: c.statement,
        confidence: c.confidence,
        polarity: c.polarity,
        created_at: datetime()
    })
    
    CREATE (tv)-[:HAS_CLAIM]->(cv)
    CREATE (c)-[:HAS_VERSION]->(cv)

    
    CREATE (fv_source)-[:CLAIMS]->(cv)
    CREATE (cv)-[:TO]->(fv_target)
    
    RETURN count(cv) as migrated_claims
    """
    
    if DRY_RUN:
        print("[DRY RUN] Would execute Claim Migration query matching factors in this version.")
    else:
        res = tx.run(q_migrate_claims, {"tvid": theme_version_id})
        count = res.single()["migrated_claims"]
        print(f"  Migrated {count} claims.")

def cleanup_legacy_relationships(tx):
    print("\n--- Cleaning up Legacy Relationships ---")
    
    # 1. Remove direct Theme -> Factor link (Legacy)
    # New path is ThemeBase -> ThemeVersion -> FactorVersion
    # Old path was Theme -> Factor (now ThemeBase -> FactorBase)
    q_clean_tf = """
    MATCH (t:ThemeBase)-[r:HAS_FACTOR]->(f:FactorBase)
    DELETE r
    RETURN count(r) as c
    """
    res = run_query(tx, q_clean_tf)
    c = res[0]['c'] if res else 0
    print(f"Deleted {c} legacy Theme->Factor relationships.")

    # 2. Remove direct Factor -> Claim link (Legacy)
    q_clean_fc = """
    MATCH (f:FactorBase)-[r:CLAIMS]->(c:ClaimBase)
    DELETE r
    RETURN count(r) as c
    """
    res = run_query(tx, q_clean_fc)
    c = res[0]['c'] if res else 0
    print(f"Deleted {c} legacy Factor->Claim relationships.")

    # 3. Remove direct Claim -> Factor link (Legacy)
    q_clean_cf = """
    MATCH (c:ClaimBase)-[r:TO]->(f:FactorBase)
    DELETE r
    RETURN count(r) as c
    """
    res = run_query(tx, q_clean_cf)
    c = res[0]['c'] if res else 0
    print(f"Deleted {c} legacy Claim->Factor relationships.")

def main():
    global DRY_RUN
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        DRY_RUN = False
        print("!!! EXECUTING MIGRATION (Changes will be persisted) !!!")
    else:
        print("--- DRY RUN MODE (No changes) ---")

    driver = GraphDatabase.driver(URI, auth=AUTH)
    
    with driver.session() as session:
        session.execute_write(migrate_themes)
        session.execute_write(cleanup_legacy_relationships)
        
    driver.close()
    print("\nMigration Completed.")

if __name__ == "__main__":
    main()
