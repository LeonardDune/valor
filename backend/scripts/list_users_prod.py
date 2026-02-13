import os
from neo4j import GraphDatabase

# Production Credentials
URI = "neo4j+s://22317c1a.databases.neo4j.io"
AUTH = ("neo4j", "Y7O7YPMSGKuLzoQD6LGcll-I9kzSEmMZDbB5aTwAEWY")

def list_users(tx):
    print("--- Listing Users ---")
    res = tx.run("MATCH (u:User) RETURN u.id as id, u.email as email, u.name as name")
    for record in res:
        print(f"ID: {record['id']}, Email: {record['email']}, Name: {record['name']}")

def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        session.execute_read(list_users)
    driver.close()

if __name__ == "__main__":
    main()
