"""Fuseki-operaties voor de disc:DiscussionThread entiteit (Epic 16)."""
import uuid
import logging
from datetime import datetime, timezone
from typing import Any

from app.services.fuseki import sparql_update, sparql_select, named_graph_uri

logger = logging.getLogger(__name__)

DISC_NS = "https://valor-ecosystem.nl/ontology/disc#"
PROV_NS = "https://www.w3.org/ns/prov#"
XSD_NS = "http://www.w3.org/2001/XMLSchema#"
VALOR_NS_BASE = "https://valor-ecosystem.nl/ontology/"


async def create_discussion_thread(
    tessera_id: str,
    design_space_id: str,
    user_id: str,
) -> str:
    """Schrijft een disc:DiscussionThread naar de named graph van de DesignSpace.

    Retourneert het thread_id (UUID).
    """
    thread_id = str(uuid.uuid4())
    thread_uri = f"urn:valor:thread:{thread_id}"
    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    user_uri = f"urn:valor:user:{user_id}"
    ds_uri = f"urn:valor:ds:{design_space_id}"
    graph_uri = named_graph_uri(design_space_id)
    timestamp = datetime.now(timezone.utc).isoformat()

    update = f"""PREFIX disc: <{DISC_NS}>
PREFIX prov: <{PROV_NS}>
PREFIX xsd:  <{XSD_NS}>
PREFIX valor: <{VALOR_NS_BASE}>

INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{thread_uri}> a disc:DiscussionThread ;
      prov:wasStartedBy <{user_uri}> ;
      prov:startedAtTime "{timestamp}"^^xsd:dateTime ;
      disc:aboutTessera <{tessera_uri}> ;
      valor:inDesignSpace <{ds_uri}> .
  }}
}}"""

    await sparql_update(update, design_space_id)
    logger.info("DiscussionThread %s aangemaakt in DesignSpace %s", thread_uri, design_space_id)
    return thread_id


async def create_thread_contribution(
    thread_id: str,
    design_space_id: str,
    user_id: str,
    contribution_type_uri: str,
    message_content: str,
    evidence_id: str | None = None,
) -> str:
    """Schrijft een disc:ThreadContribution naar de named graph van de DesignSpace.

    Koppelt de bijdrage aan de thread via disc:hasContribution.
    Retourneert het contribution_id (UUID).
    """
    contrib_id = str(uuid.uuid4())
    contrib_uri = f"urn:valor:contrib:{contrib_id}"
    thread_uri = f"urn:valor:thread:{thread_id}"
    user_uri = f"urn:valor:user:{user_id}"
    graph_uri = named_graph_uri(design_space_id)
    timestamp = datetime.now(timezone.utc).isoformat()

    escaped_content = message_content.replace("\\", "\\\\").replace('"', '\\"')

    evidence_triple = ""
    if evidence_id:
        evidence_uri = f"urn:valor:evidence:{evidence_id}"
        evidence_triple = f'\n      disc:attachesEvidence <{evidence_uri}> ;'

    update = f"""PREFIX disc: <{DISC_NS}>
PREFIX prov: <{PROV_NS}>
PREFIX xsd:  <{XSD_NS}>
PREFIX valor: <{VALOR_NS_BASE}>

INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{contrib_uri}> a disc:ThreadContribution ;
      disc:contributionType <{contribution_type_uri}> ;
      valor:messageContent "{escaped_content}"@nl ;{evidence_triple}
      prov:wasAssociatedWith <{user_uri}> ;
      prov:endedAtTime "{timestamp}"^^xsd:dateTime .
    <{thread_uri}> disc:hasContribution <{contrib_uri}> .
  }}
}}"""

    await sparql_update(update, design_space_id)
    logger.info("ThreadContribution %s toegevoegd aan thread %s", contrib_uri, thread_uri)
    return contrib_id


async def get_contributions_by_thread(
    thread_id: str,
    design_space_id: str,
) -> list[dict[str, Any]]:
    """Geeft alle disc:ThreadContributions voor een thread, gesorteerd op tijd."""
    thread_uri = f"urn:valor:thread:{thread_id}"

    query = f"""PREFIX disc: <{DISC_NS}>
PREFIX prov: <{PROV_NS}>
PREFIX valor: <{VALOR_NS_BASE}>

SELECT ?contrib_uri ?contribution_type ?message_content ?associated_with ?ended_at ?evidence WHERE {{
  <{thread_uri}> disc:hasContribution ?contrib_uri .
  ?contrib_uri disc:contributionType ?contribution_type ;
               valor:messageContent ?message_content ;
               prov:wasAssociatedWith ?associated_with ;
               prov:endedAtTime ?ended_at .
  OPTIONAL {{ ?contrib_uri disc:attachesEvidence ?evidence . }}
}}
ORDER BY ASC(?ended_at)"""

    rows = await sparql_select(query, design_space_id)
    return [
        {
            "contribution_id": row["contrib_uri"].split(":")[-1],
            "contribution_uri": row["contrib_uri"],
            "thread_id": thread_id,
            "design_space_id": design_space_id,
            "contribution_type": row["contribution_type"],
            "message_content": row["message_content"],
            "contributed_by": row["associated_with"],
            "contributed_at": row["ended_at"],
            "evidence_id": row["evidence"].split(":")[-1] if row.get("evidence") else None,
        }
        for row in rows
    ]


async def get_threads_by_tessera(
    tessera_id: str,
    design_space_id: str,
) -> list[dict[str, Any]]:
    """Geeft alle disc:DiscussionThreads voor een Tessera binnen een DesignSpace."""
    tessera_uri = f"urn:valor:tessera:{tessera_id}"

    query = f"""PREFIX disc: <{DISC_NS}>
PREFIX prov: <{PROV_NS}>

SELECT ?thread_uri ?started_by ?started_at WHERE {{
  ?thread_uri a disc:DiscussionThread ;
    disc:aboutTessera <{tessera_uri}> ;
    prov:wasStartedBy ?started_by ;
    prov:startedAtTime ?started_at .
}}
ORDER BY DESC(?started_at)"""

    rows = await sparql_select(query, design_space_id)
    return [
        {
            "thread_id": row["thread_uri"].split(":")[-1],
            "thread_uri": row["thread_uri"],
            "tessera_id": tessera_id,
            "design_space_id": design_space_id,
            "started_by": row["started_by"],
            "started_at": row["started_at"],
        }
        for row in rows
    ]
