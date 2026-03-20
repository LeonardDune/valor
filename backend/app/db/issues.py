import uuid
import asyncio
import logging
from typing import Optional

from app.db.utils import get_driver

logger = logging.getLogger(__name__)


async def create_issue_with_designspace(
    project_id: str,
    name: str,
    description: Optional[str],
    owner_id: str,
) -> dict:
    """Maakt atomair een Issue + DesignSpace aan, initialiseert Fuseki named graphs.

    Retourneert {issue_id, ds_id}.
    """
    from app.services.fuseki import initialize_design_space_graphs

    driver = get_driver()
    issue_id = str(uuid.uuid4())
    ds_id = str(uuid.uuid4())
    issue_uri = f"urn:valor:issue:{issue_id}"

    query = """
    MATCH (p:Project {id: $pid})
    MATCH (u:User {id: $uid})
    CREATE (i:Issue {
        id: $issue_id,
        name: $name,
        description: $desc,
        status: 'active',
        created_at: datetime(),
        created_by: $uid
    })
    CREATE (ds:DesignSpace {
        id: $ds_id,
        status: 'active',
        current_phase: 'exploration',
        created_at: datetime(),
        created_by: $uid
    })
    CREATE (p)-[:hasIssue]->(i)
    CREATE (i)-[:isAddressedInDesignSpace]->(ds)
    CREATE (u)-[:HAS_ROLE {role: 'admin', created_at: datetime()}]->(ds)
    RETURN i.id AS issue_id, ds.id AS ds_id
    """
    params = {
        "pid": project_id,
        "uid": owner_id,
        "issue_id": issue_id,
        "name": name,
        "desc": description,
        "ds_id": ds_id,
    }

    def _run():
        with driver.session() as session:
            result = session.run(query, params)
            record = result.single()
            if not record:
                raise RuntimeError("Issue + DesignSpace aanmaken mislukt — project of gebruiker niet gevonden.")
            return {"issue_id": record["issue_id"], "ds_id": record["ds_id"]}

    result = await asyncio.to_thread(_run)

    await initialize_design_space_graphs(result["ds_id"], issue_uri)

    return result


async def get_issue(issue_id: str) -> Optional[dict]:
    driver = get_driver()
    query = """
    MATCH (i:Issue {id: $id})
    RETURN i.id AS id, i.name AS name, i.description AS description, i.status AS status,
           i.created_at AS created_at, i.created_by AS created_by
    """

    def _run():
        with driver.session() as session:
            record = session.run(query, {"id": issue_id}).single()
            if not record:
                return None
            return {
                "id": record["id"],
                "name": record["name"],
                "description": record["description"],
                "status": record["status"],
            }

    return await asyncio.to_thread(_run)


async def update_issue(issue_id: str, name: Optional[str], description: Optional[str]) -> None:
    driver = get_driver()
    query = """
    MATCH (i:Issue {id: $id})
    SET i.name = coalesce($name, i.name),
        i.description = coalesce($desc, i.description)
    """

    def _run():
        with driver.session() as session:
            session.run(query, {"id": issue_id, "name": name, "desc": description})

    await asyncio.to_thread(_run)


async def archive_issue(issue_id: str) -> None:
    driver = get_driver()
    query = """
    MATCH (i:Issue {id: $id})
    SET i.status = 'archived'
    WITH i
    OPTIONAL MATCH (i)-[:isAddressedInDesignSpace]->(ds:DesignSpace)
    SET ds.status = 'archived'
    """

    def _run():
        with driver.session() as session:
            session.run(query, {"id": issue_id})

    await asyncio.to_thread(_run)


async def get_issues_by_project(project_id: str, user_id: str) -> list[dict]:
    """Retourneert alle Issues voor een project met DesignSpace-info en gebruikersrol."""
    driver = get_driver()
    query = """
    MATCH (p:Project {id: $pid})-[:hasIssue]->(i:Issue)-[:isAddressedInDesignSpace]->(ds:DesignSpace)
    WHERE i.status IS NULL OR i.status <> 'archived'
    MATCH (u:User {id: $uid})
    OPTIONAL MATCH (u)-[r:HAS_ROLE]->(ds)
    OPTIONAL MATCH (u)-[r_proj:HAS_ROLE]->(p)
    OPTIONAL MATCH (org:Organization)-[:OWNS]->(p)
    OPTIONAL MATCH (u)-[r_org:HAS_ROLE]->(org)
    WITH i, ds, r,
         CASE
           WHEN u.is_platform_admin = true THEN 'admin'
           WHEN r IS NOT NULL THEN r.role
           WHEN r_proj.role = 'admin' THEN 'admin'
           WHEN r_org.role = 'admin' THEN 'admin'
           ELSE 'member'
         END AS role
    RETURN i.id AS issue_id,
           ds.id AS ds_id,
           i.name AS name,
           i.description AS description,
           ds.current_phase AS current_phase,
           ds.status AS status,
           role
    ORDER BY i.created_at
    """

    def _run():
        with driver.session() as session:
            return [dict(r) for r in session.run(query, {"pid": project_id, "uid": user_id})]

    return await asyncio.to_thread(_run)
