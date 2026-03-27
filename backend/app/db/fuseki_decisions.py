"""SPARQL schrijffuncties voor deliberatie-beslissingen in Fuseki.

Verantwoordelijk voor het opslaan van valor:PhaseTransition en valor:Vote
resources in de decisions named graph van een DesignSpace.

Architectuur:
- valor:PhaseTransition is een subtype van valor:DecisionEpisode (VALOR-O §6.1, §4.7)
- Stemmen worden opgeslagen als valor:Vote resources, gekoppeld via valor:hasVote
- Alle writes zijn fire-and-forget: fouten worden gelogd als WARNING en niet gepropageerd
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from app.ontology import VALOR_NS
from app.services.fuseki import sparql_update

logger = logging.getLogger(__name__)

_XSD = "http://www.w3.org/2001/XMLSchema#"
_PROV = "https://www.w3.org/ns/prov#"


def _decisions_graph(design_space_id: str) -> str:
    return f"urn:valor:ds:{design_space_id}/decisions"


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")


async def create_phase_transition(
    design_space_id: str,
    session_id: str,
    phase: str,
    votes: list[dict],
    user_id: str,
) -> str:
    """Schrijft een valor:PhaseTransition naar de decisions named graph.

    Args:
        design_space_id: ID van de DesignSpace (zonder urn-prefix).
        session_id: ID van de VotingSession in Neo4j.
        phase: Fase-label, bijv. "refine", "ranking" of "consent".
        votes: Lijst van vote-dicts met sleutels user_id, tessera_id, vote_type.
        user_id: ID van de gebruiker die de transitie initieert.

    Returns:
        De URI string van de aangemaakte PhaseTransition.
    """
    transition_id = str(uuid.uuid4())
    transition_uri = f"urn:valor:phase-transition:{transition_id}"
    decisions_graph = _decisions_graph(design_space_id)
    ds_uri = f"urn:valor:ds:{design_space_id}"
    user_uri = f"urn:valor:user:{user_id}"
    timestamp = datetime.now(timezone.utc).isoformat()

    phase_escaped = _escape(phase)
    session_escaped = _escape(session_id)

    vote_triples = []
    for vote in votes:
        vote_id = str(uuid.uuid4())
        vote_uri = f"urn:valor:vote:{vote_id}"
        voter_uri = f"urn:valor:user:{_escape(vote['user_id'])}"
        tessera_uri = f"urn:valor:tessera:{_escape(vote['tessera_id'])}"
        vote_type_escaped = _escape(vote.get("vote_type", ""))
        vote_triples.append(
            f"""    <{vote_uri}> a <{VALOR_NS}Vote> ;
      <{VALOR_NS}castBy> <{voter_uri}> ;
      <{VALOR_NS}onTessera> <{tessera_uri}> ;
      <{VALOR_NS}voteType> "{vote_type_escaped}"^^<{_XSD}string> .
    <{transition_uri}> <{VALOR_NS}hasVote> <{vote_uri}> ."""
        )

    vote_block = "\n".join(vote_triples)

    sparql = f"""INSERT DATA {{
  GRAPH <{decisions_graph}> {{
    <{transition_uri}> a <{VALOR_NS}PhaseTransition>, <{VALOR_NS}DecisionEpisode> ;
      <{VALOR_NS}inDesignSpace> <{ds_uri}> ;
      <{VALOR_NS}forPhase> "{phase_escaped}"^^<{_XSD}string> ;
      <{VALOR_NS}sessionId> "{session_escaped}"^^<{_XSD}string> ;
      <{_PROV}startedAtTime> "{timestamp}"^^<{_XSD}dateTime> ;
      <{_PROV}wasStartedBy> <{user_uri}> .
{vote_block}
  }}
}}"""

    await sparql_update(sparql, design_space_id)
    return transition_uri
