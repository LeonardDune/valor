import os
import sys
from neo4j import GraphDatabase

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.utils import get_driver

def list_users():
    driver = get_driver()
    query = "MATCH (u:User) RETURN u.id, u.email, u.name, u.is_platform_admin"
    
    try:
        with driver.session() as session:
            result = session.run(query)
            print(f"{'Internal ID':<40} | {'Email':<30} | {'Name':<20} | {'Is Global Admin?'}")
            print("-" * 110)
            for record in result:
                email = record['u.email'] or "No Email"
                name = record['u.name'] or "No Name"
                is_admin = record['u.is_platform_admin']
                print(f"{record['u.id']:<40} | {email:<30} | {name:<20} | {is_admin}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    list_users()
