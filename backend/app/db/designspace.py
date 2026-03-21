import uuid
import asyncio
import logging
from typing import Optional

from app.db.utils import get_driver

logger = logging.getLogger(__name__)

PHASE_SEQUENCE = ["exploration", "definition", "evaluation", "decision"]


def get_design_space_meta(ds_id: str) -> dict | None:
    """Geeft current_phase en project_id voor een DesignSpace."""
    driver = get_driver()
    query = """
    MATCH (ds:DesignSpace {id: $id})
    OPTIONAL MATCH (p:Project)-[:HAS_DESIGN_SPACE]->(ds)
    RETURN ds.current_phase AS current_phase, p.id AS project_id
    """
    with driver.session() as session:
        result = session.run(query, {"id": ds_id}).single()
        if not result:
            return None
        return {
            "current_phase": result["current_phase"] or "exploration",
            "project_id": result["project_id"],
        }


def set_design_space_phase(ds_id: str, phase: str) -> None:
    """Werkt current_phase bij op de DesignSpace node."""
    driver = get_driver()
    query = """
    MATCH (ds:DesignSpace {id: $id})
    SET ds.current_phase = $phase
    """
    with driver.session() as session:
        session.run(query, {"id": ds_id, "phase": phase})


def get_design_spaces_by_project(project_id: str) -> list[dict]:
    """Geeft alle DesignSpaces terug die aan een Project gekoppeld zijn."""
    driver = get_driver()
    query = """
    MATCH (p:Project {id: $pid})-[:hasIssue]->(:Issue)-[:isAddressedInDesignSpace]->(ds:DesignSpace)
    RETURN DISTINCT ds.id AS id, ds.name AS name, ds.status AS status, ds.current_phase AS current_phase
    ORDER BY ds.created_at
    """
    with driver.session() as session:
        result = session.run(query, {"pid": project_id})
        return [dict(r) for r in result]


async def create_design_space(
    name: str,
    description: Optional[str],
    issue_uri: str,
    owner_id: str,
    project_id: Optional[str] = None,
) -> str:
    driver = get_driver()
    ds_id = str(uuid.uuid4())

    if project_id:
        query = """
        MATCH (u:User {id: $uid})
        MATCH (p:Project {id: $pid})
        CREATE (ds:DesignSpace {
            id: $id,
            name: $name,
            description: $desc,
            issue_uri: $issue_uri,
            status: 'active',
            created_at: datetime(),
            created_by: $uid
        })
        CREATE (p)-[:HAS_DESIGN_SPACE]->(ds)
        CREATE (u)-[:HAS_ROLE {role: 'admin', created_at: datetime()}]->(ds)
        RETURN ds.id as id
        """
        params = {
            "uid": owner_id,
            "pid": project_id,
            "id": ds_id,
            "name": name,
            "desc": description,
            "issue_uri": issue_uri,
        }
    else:
        query = """
        MATCH (u:User {id: $uid})
        CREATE (ds:DesignSpace {
            id: $id,
            name: $name,
            description: $desc,
            issue_uri: $issue_uri,
            status: 'active',
            created_at: datetime(),
            created_by: $uid
        })
        CREATE (u)-[:HAS_ROLE {role: 'admin', created_at: datetime()}]->(ds)
        RETURN ds.id as id
        """
        params = {
            "uid": owner_id,
            "id": ds_id,
            "name": name,
            "desc": description,
            "issue_uri": issue_uri,
        }

    with driver.session() as session:
        result = session.run(query, params)
        record = result.single()
        if not record:
            raise RuntimeError(f"DesignSpace aanmaken mislukt — gebruiker of project niet gevonden.")
        return record["id"]


async def get_designspace_with_issue(ds_id: str) -> Optional[dict]:
    """Retourneert DesignSpace properties + Issue naam/beschrijving via isAddressedInDesignSpace."""
    driver = get_driver()
    query = """
    MATCH (ds:DesignSpace {id: $id})
    OPTIONAL MATCH (ds)<-[:isAddressedInDesignSpace]-(i:Issue)
    RETURN ds.id AS ds_id,
           i.name AS name,
           i.description AS description,
           ds.current_phase AS current_phase,
           ds.status AS status,
           i.id AS issue_id
    """

    def _run():
        with driver.session() as session:
            record = session.run(query, {"id": ds_id}).single()
            if not record:
                return None
            return {
                "ds_id": record["ds_id"],
                "name": record["name"],
                "description": record["description"],
                "current_phase": record["current_phase"] or "exploration",
                "status": record["status"],
                "issue_id": record["issue_id"],
            }

    return await asyncio.to_thread(_run)


async def get_designspace_members(ds_id: str) -> list[dict]:
    driver = get_driver()
    query = """
    MATCH (u:User)-[r:HAS_ROLE]->(ds:DesignSpace {id: $id})
    RETURN u.id AS id, u.name AS name, u.email AS email, r.role AS role
    """

    def _run():
        with driver.session() as session:
            return [dict(r) for r in session.run(query, {"id": ds_id})]

    return await asyncio.to_thread(_run)


async def add_designspace_member(ds_id: str, email: str, role: str) -> None:
    from app.db.organizations import create_user
    await create_user(email)
    driver = get_driver()
    query = """
    MATCH (u:User {email: toLower($email)})
    MATCH (ds:DesignSpace {id: $id})
    MERGE (u)-[r:HAS_ROLE]->(ds)
    SET r.role = $role, r.updated_at = datetime()
    """

    def _run():
        with driver.session() as session:
            session.run(query, {"email": email, "id": ds_id, "role": role})

    await asyncio.to_thread(_run)


async def update_designspace_member_role(ds_id: str, user_id: str, role: str) -> None:
    driver = get_driver()
    query = """
    MATCH (u:User {id: $uid})-[r:HAS_ROLE]->(ds:DesignSpace {id: $id})
    SET r.role = $role, r.updated_at = datetime()
    """

    def _run():
        with driver.session() as session:
            session.run(query, {"uid": user_id, "id": ds_id, "role": role})

    await asyncio.to_thread(_run)


async def remove_designspace_member(ds_id: str, user_id: str) -> None:
    driver = get_driver()
    query = """
    MATCH (u:User {id: $uid})-[r:HAS_ROLE]->(ds:DesignSpace {id: $id})
    DELETE r
    """

    def _run():
        with driver.session() as session:
            session.run(query, {"uid": user_id, "id": ds_id})

    await asyncio.to_thread(_run)


async def get_project_id_by_designspace(ds_id: str) -> Optional[str]:
    driver = get_driver()
    query = """
    MATCH (p:Project)-[:hasIssue]->(:Issue)-[:isAddressedInDesignSpace]->(ds:DesignSpace {id: $id})
    RETURN p.id AS pid
    """

    def _run():
        with driver.session() as session:
            record = session.run(query, {"id": ds_id}).single()
            return record["pid"] if record else None

    return await asyncio.to_thread(_run)
