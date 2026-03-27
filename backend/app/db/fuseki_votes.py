import uuid
import logging
from datetime import datetime, timezone

from app.ontology import VALOR_NS
from app.services.fuseki import sparql_update

logger = logging.getLogger(__name__)

_XSD = "http://www.w3.org/2001/XMLSchema#"
_PROV = "https://www.w3.org/ns/prov#"


def _decisions_graph(ds_id: str) -> str:
    return f"urn:valor:ds:{ds_id}/decisions"


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")


async def write_consent_vote_to_fuseki(
    ds_id: str,
    session_id: str,
    tessera_base_id: str,
    user_id: str,
    vote_type: str,
    motivation: str | None = None,
) -> None:
    vote_id = str(uuid.uuid4())
    vote_uri = f"urn:valor:vote:{vote_id}"
    user_uri = f"urn:valor:user:{_escape(user_id)}"
    tessera_uri = f"urn:valor:tessera:{_escape(tessera_base_id)}"
    timestamp = datetime.now(timezone.utc).isoformat()

    vote_type_escaped = _escape(vote_type)
    session_escaped = _escape(session_id)
    decisions_graph = _decisions_graph(ds_id)

    motivation_triple = ""
    if motivation:
        motivation_triple = f'\n      <{VALOR_NS}motivation> "{_escape(motivation)}"^^<{_XSD}string> ;'

    sparql = f"""INSERT DATA {{
  GRAPH <{decisions_graph}> {{
    <{vote_uri}> a <{VALOR_NS}Vote> ;
      <{VALOR_NS}castBy> <{user_uri}> ;
      <{VALOR_NS}onTessera> <{tessera_uri}> ;
      <{VALOR_NS}voteType> "{vote_type_escaped}"^^<{_XSD}string> ;
      <{VALOR_NS}sessionId> "{session_escaped}"^^<{_XSD}string> ;{motivation_triple}
      <{_PROV}atTime> "{timestamp}"^^<{_XSD}dateTime> .
  }}
}}"""

    await sparql_update(sparql, ds_id)
