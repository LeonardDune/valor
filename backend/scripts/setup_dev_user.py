import os
import sys
import argparse
from dotenv import load_dotenv
from supabase import create_client, Client
from neo4j import GraphDatabase

# Load .env explicitly
load_dotenv("backend/.env")

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_KEY:
    print("Error: SUPABASE_SERVICE_KEY not found in backend/.env")
    sys.exit(1)

def setup_user(email: str):
    print(f"1. Fetching UUID for {email} from Supabase...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # List users to find the ID (Admin API)
    # Note: supabase-py admin usage might vary by version. 
    # Using auth.admin.list_users() standard pattern.
    try:
        # Paginating just in case, though usually dev has few users.
        response = supabase.auth.admin.list_users(page=1, per_page=100)
        found_user = next((u for u in response if u.email == email), None)
        
        if not found_user:
            print(f"⚠️ User {email} not found. Creating new Dev User...")
            # Auto-create user with a default dev password
            default_password = "ValorDevPassword123!"
            attributes = {
                "email": email,
                "password": default_password,
                "email_confirm": True
            }
            try:
                new_user = supabase.auth.admin.create_user(attributes)
                user_id = new_user.user.id # Structure might depend on lib version, usually response.user.id or just response.id
                print(f"✅ Created User! Password: {default_password}")
            except Exception as e:
                # Fallback for library variations
                print(f"Creation attempt details: {e}")
                # Try accessing .user directly if previous failed or check attributes
                sys.exit(1)
        else:
             user_id = found_user.id
        
        print(f"✅ UUID: {user_id}")
        
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        sys.exit(1)

    print(f"\n2. Configuring User in Neo4j ({NEO4J_URI})...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    
    with driver.session() as session:
        # A. Remove the dummy admin if it exists
        session.run("MATCH (u:User {id: 'user-dev-admin'}) DETACH DELETE u")
        
        # B. Upsert the Real User
        # We merge on ID to ensure uniqueness
        query = """
        MERGE (u:User {id: $uid})
        ON CREATE SET 
            u.created_at = datetime(),
            u.email = $email,
            u.name = $email,
            u.is_platform_admin = true
        ON MATCH SET 
            u.email = $email,
            u.is_platform_admin = true
            
        WITH u
        MATCH (o:Organization {id: 'org-dev-valor'})
        MERGE (u)-[r:HAS_ROLE]->(o)
        SET r.role = 'admin'
        
        RETURN u.id as id, u.email as email, u.is_platform_admin as isAdmin
        """
        
        result = session.run(query, uid=user_id, email=email).single()
        print(f"✅ User Configured: {result['email']} (Admin: {result['isAdmin']})")
        print("   Linked to 'Valor Development' organization.")

    driver.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Promote a Supabase user to Dev Admin.")
    parser.add_argument("email", help="The email of the Supabase user")
    args = parser.parse_args()
    
    setup_user(args.email)
