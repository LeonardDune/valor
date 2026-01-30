import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load .env explicitly
load_dotenv()

URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))

def init_db():
    print(f"Connecting to {URI}...")
    
    try:
        driver = GraphDatabase.driver(URI, auth=AUTH)
        driver.verify_connectivity()
    except Exception as e:
        print(f"FATAL: Could not connect to Neo4j: {e}")
        sys.exit(1)

    with driver.session() as session:
        # 1. Safety Check
        count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
        print(f"Current Node Count: {count}")
        
        if count > 0:
            print("\n!!! WARNING !!!")
            print("The database is NOT empty.")
            print("To prevent accidental data loss on Production, this script will STOP.")
            print("Please ensure you are connected to the new, empty VALOR-DEV instance.")
            print("If you really want to overwrite this DB, wipe it manually first.")
            driver.close()
            sys.exit(1)
            
        print("Database is empty. Safe to proceed.")
        
        # 2. Apply Schema
        print("\nApplying Constraints & Indexes...")
        # Read schema file
        with open("app/db/schema.cypher", "r") as f:
            schema_script = f.read()
            
        statements = [s.strip() for s in schema_script.split(";") if s.strip()]
        
        for stmt in statements:
            print(f"Executing: {stmt[:50]}...")
            try:
                session.run(stmt)
            except Exception as e:
                print(f"Error executing statement: {e}")

        # 3. Seed Basic Data (Optional)
        print("\nSeeding basic environment data...")
        # Create a default Organization and Admin User if they don't exist (which they don't, cause it's empty)
        admin_email = os.getenv("DEV_ADMIN_EMAIL", "admin@valor.dev")
        
        session.run("""
            CREATE (o:Organization {
                id: 'org-dev-valor', 
                name: 'Valor Development', 
                status: 'active',
                created_at: datetime()
            })
            CREATE (u:User {
                id: 'user-dev-admin',
                email: $email,
                name: 'Dev Admin',
                is_platform_admin: true,
                created_at: datetime()
            })
            CREATE (u)-[:HAS_ROLE {role: 'admin'}]->(o)
        """, {"email": admin_email})
        print(f"Created Org: 'Valor Development' and User: '{admin_email}'")

    driver.close()
    print("\n✅ Initialization Complete. Ready for Development.")

if __name__ == "__main__":
    init_db()
