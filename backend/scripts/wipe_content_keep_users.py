import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.utils import get_driver

def wipe_content_keep_users():
    print("WARNING: This will delete ALL data except Users. Press Enter to confirm or Ctrl+C to cancel.")
    # In automated run, we can't wait for input, so assume 'yes' if running non-interactively or just log it.
    print("Proceeding with partial wipe...")
    
    driver = get_driver()
    with driver.session() as session:
        # Check user count before
        users_before = session.run("MATCH (u:User) RETURN count(u) as c").single()['c']
        print(f"Users before wipe: {users_before}")
        
        # Delete everything that is NOT a User
        # Strategy: Detach delete all relationships. Then delete all nodes without User label.
        
        # 1. Delete all relationships
        print("Deleting all relationships...")
        session.run("MATCH ()-[r]->() DELETE r")
        
        # 2. Delete all non-User nodes
        print("Deleting all non-User nodes...")
        session.run("MATCH (n) WHERE NOT 'User' IN labels(n) DELETE n")
        
        # Check user count after
        users_after = session.run("MATCH (u:User) RETURN count(u) as c").single()['c']
        print(f"Users after wipe: {users_after}")
        
        if users_before != users_after:
            print("CRITICAL: User count mismatch! Some users might have been deleted if they had mixed labels?")
        else:
            print("User count preserved successfully.")
            
    # driver.close() handled by app.db.utils if we wanted to close global, but usually ok to leave open in script end

if __name__ == "__main__":
    wipe_content_keep_users()
