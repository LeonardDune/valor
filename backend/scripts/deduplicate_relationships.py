from app.db.utils import get_driver, close_driver
import logging
import argparse
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REL_TYPES_TO_DEDUPLICATE = [
    "HAS_VERSION", 
    "HAS_SESSION", 
    "HAS_FACTOR", 
    "HAS_CLAIM",
    "HAS_ACTIVE_VERSION",
    "HAS_THEME",
    "HAS_THREAD",
    "IS_VERSION_OF",
    "CREATED",
    "AUTHORED",
    "BELONGS_TO",
    "RESULTED_IN",
    "DECIDED_BY",
    "HAS_DECISION"
]

async def deduplicate_relationships(dry_run=True):
    driver = get_driver()
    try:
        with driver.session() as session:
            for rel_type in REL_TYPES_TO_DEDUPLICATE:
                logger.info(f"Deduplicating relationship: {rel_type} (Dry-run: {dry_run})")
                
                # Find duplicates
                find_query = f"""
                MATCH (a)-[r:{rel_type}]->(b)
                WITH a, b, collect(r) as rels
                WHERE size(rels) > 1
                RETURN count(*) as duplicate_pairs, sum(size(rels) - 1) as total_to_delete
                """
                
                res = session.run(find_query).single()
                if res and res['total_to_delete'] > 0:
                    logger.info(f"Found {res['duplicate_pairs']} pairs with {res['total_to_delete']} redundant {rel_type} relationships.")
                    
                    if not dry_run:
                        delete_query = f"""
                        MATCH (a)-[r:{rel_type}]->(b)
                        WITH a, b, collect(r) as rels
                        WHERE size(rels) > 1
                        UNWIND rels[1..] as duplicate
                        DELETE duplicate
                        RETURN count(*) as deleted_count
                        """
                        del_res = session.run(delete_query).single()
                        logger.info(f"Deleted {del_res['deleted_count']} relationships.")
                else:
                    logger.info(f"No duplicates found for {rel_type}.")
                    
    except Exception as e:
        logger.error(f"Failed to deduplicate relationships: {e}")
    finally:
        close_driver()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deduplicate Neo4j relationships")
    parser.add_argument("--run", action="store_true", help="Actually run the deletion (default is dry-run)")
    args = parser.parse_args()
    
    asyncio.run(deduplicate_relationships(dry_run=not args.run))
