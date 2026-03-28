"""SPARQL-operaties voor fase-snapshots in Fuseki.

Na elke deliberatie-finalisatie:
1. copy_asis_to_snapshot      — kopieert asis volledig naar phase/{session_id}
2. annotate_snapshot          — voegt phaseOutcome (Accepted/Rejected) per tessera toe
3. register_snapshot_in_decisions — registreert snapshot in decisions-graph
4. prune_rejected_from_asis   — verwijdert afgewezen tesserae + afhankelijke claims uit asis
5. get_phase_snapshots        — retourneert lijst van snapshots voor een DesignSpace
"""
import logging
from datetime import datetime, timezone

from app.ontology import VALOR_NS
from app.services.fuseki import sparql_update, sparql_select_global

logger = logging.getLogger(__name__)

_XSD  = "http://www.w3.org/2001/XMLSchema#"
_PROV = "https://www.w3.org/ns/prov#"


def _asis_graph(ds_id: str) -> str:
    return f"urn:valor:ds:{ds_id}/asis"


def _phase_graph(ds_id: str, session_id: str) -> str:
    return f"urn:valor:ds:{ds_id}/phase/{session_id}"


def _decisions_graph(ds_id: str) -> str:
    return f"urn:valor:ds:{ds_id}/decisions"


def _tessera_uri(base_id: str) -> str:
    return f"urn:valor:tessera:{base_id}"


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")


async def copy_asis_to_snapshot(ds_id: str, session_id: str) -> str:
    """Kopieert de volledige asis-graph naar een nieuwe phase-graph.

    Retourneert de phase-graph URI.
    """
    asis  = _asis_graph(ds_id)
    phase = _phase_graph(ds_id, session_id)
    sparql = f"COPY <{asis}> TO <{phase}>"
    await sparql_update(sparql, ds_id)
    return phase


async def annotate_snapshot(
    ds_id: str,
    session_id: str,
    accepted_ids: list[str],
    rejected_ids: list[str],
) -> None:
    """Voegt phaseOutcome-triples en metadata toe aan de snapshot-graph."""
    phase = _phase_graph(ds_id, session_id)
    snapshot_uri = f"urn:valor:phase-snapshot:{session_id}"
    timestamp = datetime.now(timezone.utc).isoformat()

    outcome_triples = []
    for tid in accepted_ids:
        turi = _tessera_uri(tid)
        outcome_triples.append(f"<{turi}> <{VALOR_NS}phaseOutcome> <{VALOR_NS}Accepted> .")
    for tid in rejected_ids:
        turi = _tessera_uri(tid)
        outcome_triples.append(f"<{turi}> <{VALOR_NS}phaseOutcome> <{VALOR_NS}Rejected> .")

    outcomes_block = "\n    ".join(outcome_triples)

    sparql = f"""INSERT DATA {{
  GRAPH <{phase}> {{
    <{snapshot_uri}> a <{VALOR_NS}PhaseSnapshot> ;
      <{VALOR_NS}sessionId> "{_escape(session_id)}"^^<{_XSD}string> ;
      <{_PROV}generatedAtTime> "{timestamp}"^^<{_XSD}dateTime> .
    {outcomes_block}
  }}
}}"""
    await sparql_update(sparql, ds_id)


async def register_snapshot_in_decisions(
    ds_id: str,
    session_id: str,
    accepted_count: int,
    rejected_count: int,
) -> None:
    """Registreert de snapshot in de decisions-graph zodat die opvraagbaar is."""
    decisions    = _decisions_graph(ds_id)
    phase        = _phase_graph(ds_id, session_id)
    snapshot_uri = f"urn:valor:phase-snapshot:{session_id}"
    ds_uri       = f"urn:valor:ds:{ds_id}"
    timestamp    = datetime.now(timezone.utc).isoformat()

    sparql = f"""INSERT DATA {{
  GRAPH <{decisions}> {{
    <{snapshot_uri}> a <{VALOR_NS}PhaseSnapshot> ;
      <{VALOR_NS}inDesignSpace> <{ds_uri}> ;
      <{VALOR_NS}sessionId> "{_escape(session_id)}"^^<{_XSD}string> ;
      <{VALOR_NS}graphUri> "{_escape(phase)}"^^<{_XSD}string> ;
      <{VALOR_NS}acceptedCount> "{accepted_count}"^^<{_XSD}integer> ;
      <{VALOR_NS}rejectedCount> "{rejected_count}"^^<{_XSD}integer> ;
      <{_PROV}generatedAtTime> "{timestamp}"^^<{_XSD}dateTime> .
  }}
}}"""
    await sparql_update(sparql, ds_id)


async def prune_rejected_from_asis(ds_id: str, rejected_ids: list[str]) -> None:
    """Verwijdert afgewezen tesserae en hun afhankelijke claims uit asis.

    Stap 1: verwijder claims waarvan fromFactor of toFactor afgewezen is.
    Stap 2: verwijder de afgewezen tesserae zelf (als subject).
    """
    if not rejected_ids:
        return

    asis = _asis_graph(ds_id)
    uris = ", ".join(f"<{_tessera_uri(tid)}>" for tid in rejected_ids)

    # Stap 1: verwijder claims die verwijzen naar afgewezen factoren
    sparql_claims = f"""DELETE {{
  GRAPH <{asis}> {{
    ?claim ?p ?o .
  }}
}}
WHERE {{
  GRAPH <{asis}> {{
    ?claim ?p ?o .
    {{
      ?claim <{VALOR_NS}fromFactor> ?factor .
      FILTER(?factor IN ({uris}))
    }}
    UNION
    {{
      ?claim <{VALOR_NS}toFactor> ?factor .
      FILTER(?factor IN ({uris}))
    }}
  }}
}}"""
    await sparql_update(sparql_claims, ds_id)

    # Stap 2: verwijder de afgewezen tesserae zelf
    sparql_tesserae = f"""DELETE {{
  GRAPH <{asis}> {{
    ?s ?p ?o .
  }}
}}
WHERE {{
  GRAPH <{asis}> {{
    ?s ?p ?o .
    FILTER(?s IN ({uris}))
  }}
}}"""
    await sparql_update(sparql_tesserae, ds_id)


async def get_phase_snapshots(ds_id: str) -> list[dict]:
    """Retourneert alle fase-snapshots voor een DesignSpace, gesorteerd op tijd."""
    decisions = _decisions_graph(ds_id)
    rows = await sparql_select_global(f"""
SELECT ?snapshotUri ?sessionId ?graphUri ?generatedAt ?acceptedCount ?rejectedCount WHERE {{
  GRAPH <{decisions}> {{
    ?snapshotUri a <{VALOR_NS}PhaseSnapshot> ;
      <{VALOR_NS}sessionId> ?sessionId ;
      <{VALOR_NS}graphUri> ?graphUri ;
      <{_PROV}generatedAtTime> ?generatedAt .
    OPTIONAL {{ ?snapshotUri <{VALOR_NS}acceptedCount> ?acceptedCount }}
    OPTIONAL {{ ?snapshotUri <{VALOR_NS}rejectedCount> ?rejectedCount }}
  }}
}}
ORDER BY ASC(?generatedAt)
""")
    return [
        {
            "session_id":     r["sessionId"],
            "graph_uri":      r["graphUri"],
            "created_at":     r["generatedAt"],
            "accepted_count": int(r.get("acceptedCount", 0)),
            "rejected_count": int(r.get("rejectedCount", 0)),
        }
        for r in rows
    ]
