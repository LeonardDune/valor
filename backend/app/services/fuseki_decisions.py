"""Fuseki-operaties voor DecisionEpisodes en stemmen (US-5.2).

Alle schrijfoperaties gaan naar de `decisions` named graph van de DesignSpace.
Quorumdrempel is configureerbaar via env var VALOR_QUORUM_THRESHOLD (default 0.5).
"""
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.ontology import VALOR_NS
from app.services.fuseki import sparql_select, sparql_update, record_provenance_activity

logger = logging.getLogger(__name__)

PROV_NS = "https://www.w3.org/ns/prov#"
XSD_NS = "http://www.w3.org/2001/XMLSchema#"

QUORUM_THRESHOLD = float(os.getenv("VALOR_QUORUM_THRESHOLD", "0.5"))

_VOTE_TYPE_URIS = {
    "Accept": f"{VALOR_NS}AcceptVote",
    "Reject": f"{VALOR_NS}RejectVote",
    "Defer":  f"{VALOR_NS}DeferVote",
}

_VOTE_URI_TO_TYPE = {v: k for k, v in _VOTE_TYPE_URIS.items()}


def _decisions_graph(ds_id: str) -> str:
    return f"urn:valor:ds:{ds_id}/decisions"


async def create_or_get_decision_episode(
    ds_id: str,
    tessera_uri: str,
    created_by_uri: str,
) -> str:
    """Geeft de URI van een bestaande open DecisionEpisode voor de Tessera,
    of maakt een nieuwe aan als er nog geen is.

    Retourneert episode_uri.
    """
    decisions_graph = _decisions_graph(ds_id)

    rows = await sparql_select(
        f"""SELECT ?episode WHERE {{
          GRAPH <{decisions_graph}> {{
            ?episode a <{VALOR_NS}DecisionEpisode> ;
                     <{VALOR_NS}concernsTessera> <{tessera_uri}> ;
                     <{VALOR_NS}episodeStatus> <{VALOR_NS}OpenEpisode> .
          }}
        }}""",
        ds_id,
    )

    if rows:
        return rows[0]["episode"]

    episode_id = str(uuid.uuid4())
    episode_uri = f"urn:valor:episode:{episode_id}"
    created_at = datetime.now(timezone.utc).isoformat()

    update = f"""INSERT DATA {{
  GRAPH <{decisions_graph}> {{
    <{episode_uri}> a <{VALOR_NS}DecisionEpisode> ;
      <{VALOR_NS}concernsTessera> <{tessera_uri}> ;
      <{VALOR_NS}episodeStatus> <{VALOR_NS}OpenEpisode> ;
      <{VALOR_NS}createdBy> <{created_by_uri}> ;
      <{VALOR_NS}createdAt> "{created_at}"^^<{XSD_NS}dateTime> .
  }}
}}"""
    await sparql_update(update, ds_id)

    logger.info("DecisionEpisode aangemaakt: %s voor Tessera %s", episode_uri, tessera_uri)
    return episode_uri


async def cast_vote(
    ds_id: str,
    episode_uri: str,
    tessera_uri: str,
    voter_uri: str,
    vote_type: str,
) -> str:
    """Schrijft een valor:Vote naar de decisions graph.

    Een gebruiker kan per episode maar één stem uitbrengen — bestaande stem
    wordt vervangen (idempotent per kiezer per episode).

    Retourneert vote_uri.
    """
    vote_type_uri = _VOTE_TYPE_URIS.get(vote_type)
    if not vote_type_uri:
        raise ValueError(f"Ongeldig vote_type '{vote_type}'. Geldige waarden: {sorted(_VOTE_TYPE_URIS)}.")

    decisions_graph = _decisions_graph(ds_id)
    voted_at = datetime.now(timezone.utc).isoformat()

    # Verwijder bestaande stem van dezelfde kiezer op hetzelfde episode
    delete_existing = f"""DELETE {{
  GRAPH <{decisions_graph}> {{
    ?existing_vote a <{VALOR_NS}Vote> ;
      <{VALOR_NS}castBy> <{voter_uri}> ;
      <{VALOR_NS}inEpisode> <{episode_uri}> ;
      <{VALOR_NS}voteType> ?old_type ;
      <{VALOR_NS}votedAt> ?old_at .
  }}
}}
WHERE {{
  GRAPH <{decisions_graph}> {{
    ?existing_vote a <{VALOR_NS}Vote> ;
      <{VALOR_NS}castBy> <{voter_uri}> ;
      <{VALOR_NS}inEpisode> <{episode_uri}> ;
      <{VALOR_NS}voteType> ?old_type ;
      <{VALOR_NS}votedAt> ?old_at .
  }}
}}"""
    await sparql_update(delete_existing, ds_id)

    vote_id = str(uuid.uuid4())
    vote_uri = f"urn:valor:vote:{vote_id}"

    insert = f"""INSERT DATA {{
  GRAPH <{decisions_graph}> {{
    <{vote_uri}> a <{VALOR_NS}Vote> ;
      <{VALOR_NS}castBy> <{voter_uri}> ;
      <{VALOR_NS}inEpisode> <{episode_uri}> ;
      <{VALOR_NS}voteType> <{vote_type_uri}> ;
      <{VALOR_NS}votedAt> "{voted_at}"^^<{XSD_NS}dateTime> .
    <{episode_uri}> <{VALOR_NS}hasVote> <{vote_uri}> .
  }}
}}"""
    await sparql_update(insert, ds_id)

    logger.info("Vote %s uitgebracht: %s door %s op episode %s", vote_uri, vote_type, voter_uri, episode_uri)
    return vote_uri


async def evaluate_quorum(
    ds_id: str,
    episode_uri: str,
    tessera_uri: str,
    graph_uri: str,
) -> Optional[str]:
    """Berekent of quorum bereikt is en past epistemische status aan indien nodig.

    Telt Accept en Reject stemmen. Als één van de twee > QUORUM_THRESHOLD van het
    totaal aantal stemmen, sluit het episode en wijzigt de epistemische status.

    Retourneert de nieuwe status-label als quorum bereikt is, anders None.
    """
    from app.services.ontology_cache import get_status_label_to_uri, get_status_uri_to_label

    decisions_graph = _decisions_graph(ds_id)

    vote_rows = await sparql_select(
        f"""SELECT ?voteType (COUNT(?vote) AS ?count) WHERE {{
          GRAPH <{decisions_graph}> {{
            ?vote a <{VALOR_NS}Vote> ;
              <{VALOR_NS}inEpisode> <{episode_uri}> ;
              <{VALOR_NS}voteType> ?voteType .
          }}
        }}
        GROUP BY ?voteType""",
        ds_id,
    )

    counts: dict[str, int] = {}
    for row in vote_rows:
        vtype_uri = row["voteType"]
        label = _VOTE_URI_TO_TYPE.get(vtype_uri, vtype_uri)
        counts[label] = int(row["count"])

    total = sum(counts.values())
    if total == 0:
        return None

    accept_count = counts.get("Accept", 0)
    reject_count = counts.get("Reject", 0)

    new_status_label: Optional[str] = None
    if accept_count / total > QUORUM_THRESHOLD:
        new_status_label = "Accepted"
    elif reject_count / total > QUORUM_THRESHOLD:
        new_status_label = "Rejected"

    if not new_status_label:
        return None

    status_label_to_uri = get_status_label_to_uri()
    new_status_uri = status_label_to_uri.get(new_status_label)
    if not new_status_uri:
        logger.warning("Status '%s' niet gevonden in ontologie, quorum niet toegepast.", new_status_label)
        return None

    # Haal huidige status op uit de correcte graph
    status_rows = await sparql_select(
        f"""SELECT ?status WHERE {{
          GRAPH <{graph_uri}> {{
            <{tessera_uri}> <{VALOR_NS}epistemicStatus> ?status .
          }}
        }}""",
        ds_id,
    )
    if not status_rows:
        logger.warning("Tessera %s niet gevonden in graph %s voor quorum-update.", tessera_uri, graph_uri)
        return None

    current_uri = status_rows[0]["status"]

    # Update epistemische status in de tessera-graph
    await sparql_update(
        f"""DELETE {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> <{VALOR_NS}epistemicStatus> <{current_uri}> .
  }}
}}
INSERT {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> <{VALOR_NS}epistemicStatus> <{new_status_uri}> .
  }}
}}
WHERE {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> <{VALOR_NS}epistemicStatus> <{current_uri}> .
  }}
}}""",
        ds_id,
    )

    # Sluit het episode
    closed_at = datetime.now(timezone.utc).isoformat()
    await sparql_update(
        f"""DELETE {{
  GRAPH <{decisions_graph}> {{
    <{episode_uri}> <{VALOR_NS}episodeStatus> <{VALOR_NS}OpenEpisode> .
  }}
}}
INSERT {{
  GRAPH <{decisions_graph}> {{
    <{episode_uri}> <{VALOR_NS}episodeStatus> <{VALOR_NS}ClosedEpisode> ;
                    <{VALOR_NS}closedAt> "{closed_at}"^^<{XSD_NS}dateTime> ;
                    <{VALOR_NS}resolvedWith> <{new_status_uri}> .
  }}
}}
WHERE {{
  GRAPH <{decisions_graph}> {{
    <{episode_uri}> <{VALOR_NS}episodeStatus> <{VALOR_NS}OpenEpisode> .
  }}
}}""",
        ds_id,
    )

    logger.info(
        "Quorum bereikt op episode %s: Tessera %s → %s",
        episode_uri, tessera_uri, new_status_label,
    )
    return new_status_label
