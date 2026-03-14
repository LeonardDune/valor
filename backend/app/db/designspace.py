import uuid
import logging
from typing import Optional

from app.db.utils import get_driver

logger = logging.getLogger(__name__)


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
