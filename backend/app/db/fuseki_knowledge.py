"""SPARQL-gebaseerde lees- en schrijffuncties voor Factors en Claims in Fuseki.

Vervangt de Neo4j knowledge-laag (app/db/knowledge.py) voor inhoudelijke kennisdata.

Architectuur na US-11.2:
- Neo4j : User, Org, Project, Theme, ThemeVersion, DesignSpace — identiteit + RBAC
- Fuseki: Factors, Claims als valor:Tessera — alle inhoudelijke kennisdata

Elke Tessera heeft een `valor:baseId` property (plain string UUID).
Dit is de canonieke `id` die de API teruggeeft, ongeacht de URI-structuur.
"""
import asyncio
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from app.ontology import VALOR_NS
from app.db.utils import get_driver
from app.services.fuseki import sparql_select_global, sparql_update

logger = logging.getLogger(__name__)

_XSD = "http://www.w3.org/2001/XMLSchema#"
_TESSERA_PREFIX = "urn:valor:tessera:"


# ---------------------------------------------------------------------------
# URI helpers
# ---------------------------------------------------------------------------

def _tessera_uri(tessera_id: str) -> str:
    return f"{_TESSERA_PREFIX}{tessera_id}"


def _ds_baseline_graph(ds_id: str) -> str:
    return f"urn:valor:ds:{ds_id}/baseline"


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")


# ---------------------------------------------------------------------------
# Neo4j hiërarchie-lookups (geen kennisdata)
# ---------------------------------------------------------------------------

def _get_project_id_for_designspace_sync(ds_id: str) -> Optional[str]:
    driver = get_driver()
    with driver.session() as s:
        r = s.run(
            "MATCH (p:Project)-[:hasIssue]->(:Issue)-[:isAddressedInDesignSpace]->(ds:DesignSpace {id: $ds_id}) RETURN p.id AS pid",
            {"ds_id": ds_id},
        ).single()
    return r["pid"] if r else None


async def get_project_id_for_designspace(ds_id: str) -> Optional[str]:
    return await asyncio.to_thread(_get_project_id_for_designspace_sync, ds_id)


# ---------------------------------------------------------------------------
# Fuseki context-lookups
# ---------------------------------------------------------------------------

async def get_designspace_id_for_tessera(tessera_id: str) -> Optional[str]:
    """Zoekt de DesignSpace ID voor een Tessera via Fuseki SPARQL (valor:inDesignSpace)."""
    tessera_uri = _tessera_uri(tessera_id)
    rows = await sparql_select_global(
        f"SELECT ?ds WHERE {{ GRAPH ?g {{ <{tessera_uri}> <{VALOR_NS}inDesignSpace> ?ds }} }}"
    )
    if not rows:
        return None
    ds_uri = rows[0]["ds"]
    prefix = "urn:valor:ds:"
    return ds_uri[len(prefix):] if ds_uri.startswith(prefix) else ds_uri


async def _find_tessera_uri_by_base_id(ds_id: str, base_id: str) -> Optional[str]:
    """Vindt de werkelijke tessera-URI voor een base_id in de baseline-graph (voor claim-schrijven)."""
    baseline_graph = _ds_baseline_graph(ds_id)
    rows = await sparql_select_global(
        f'SELECT ?t WHERE {{ GRAPH <{baseline_graph}> {{ ?t <{VALOR_NS}baseId> "{base_id}" }} }}'
    )
    return rows[0]["t"] if rows else _tessera_uri(base_id)


# ---------------------------------------------------------------------------
# Factor reads (SPARQL)
# ---------------------------------------------------------------------------

async def _sparql_get_factors(ds_id: str) -> list[dict]:
    baseline_graph = _ds_baseline_graph(ds_id)
    rows = await sparql_select_global(f"""
SELECT ?tessera ?baseId ?name ?role ?description WHERE {{
  GRAPH <{baseline_graph}> {{
    ?tessera a <{VALOR_NS}Tessera> ;
             <{VALOR_NS}baseId> ?baseId ;
             <{VALOR_NS}claimContent> ?name ;
             <{VALOR_NS}factorRole> ?role .
    OPTIONAL {{ ?tessera <{VALOR_NS}description> ?description }}
    FILTER NOT EXISTS {{ ?tessera <{VALOR_NS}fromFactor> ?x }}
  }}
}}
""")
    return [
        {
            "id": row["baseId"],
            "version_id": row["baseId"],
            "name": row["name"],
            "description": row.get("description"),
            "type": row.get("role"),
            "theme_id": None,
            "thread_id": None,
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Factor writes (SPARQL)
# ---------------------------------------------------------------------------

async def create_factor_fuseki(
    ds_id: str,
    name: str,
    role: str,
    user_id: str,
    description: Optional[str] = None,
) -> str:
    """Maakt een nieuwe Factor-Tessera aan in Fuseki. Retourneert de base_id."""
    base_id = str(uuid.uuid4())
    tessera_uri = _tessera_uri(base_id)
    baseline_graph = _ds_baseline_graph(ds_id)
    user_uri = f"urn:valor:user:{user_id}"
    claimed_at = datetime.now(timezone.utc).isoformat()
    proposed_uri = f"{VALOR_NS}ProposedStatus"
    desc_triple = (
        f'<{tessera_uri}> <{VALOR_NS}description> "{_escape(description)}"@nl .'
        if description else ""
    )

    sparql = f"""INSERT DATA {{
  GRAPH <{baseline_graph}> {{
    <{tessera_uri}> a <{VALOR_NS}Tessera> ;
      <{VALOR_NS}baseId> "{base_id}" ;
      <{VALOR_NS}claimContent> "{_escape(name)}"@nl ;
      <{VALOR_NS}factorRole> "{_escape(role)}" ;
      <{VALOR_NS}epistemicStatus> <{proposed_uri}> ;
      <{VALOR_NS}claimedBy> <{user_uri}> ;
      <{VALOR_NS}claimedAt> "{claimed_at}"^^<{_XSD}dateTime> ;
      <{VALOR_NS}inDesignSpace> <urn:valor:ds:{ds_id}> .
    {desc_triple}
  }}
}}"""
    await sparql_update(sparql, ds_id)
    return base_id


async def update_factor_fuseki(
    tessera_id: str,
    ds_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    role: Optional[str] = None,
) -> None:
    """Werkt een bestaande Factor-Tessera bij in Fuseki (alleen opgegeven velden)."""
    tessera_uri = _tessera_uri(tessera_id)
    baseline_graph = _ds_baseline_graph(ds_id)

    deletes, inserts, optionals = [], [], []

    if name is not None:
        deletes.append(f"<{tessera_uri}> <{VALOR_NS}claimContent> ?oldName .")
        inserts.append(f'<{tessera_uri}> <{VALOR_NS}claimContent> "{_escape(name)}"@nl .')
        optionals.append(f"OPTIONAL {{ <{tessera_uri}> <{VALOR_NS}claimContent> ?oldName }}")

    if role is not None:
        deletes.append(f"<{tessera_uri}> <{VALOR_NS}factorRole> ?oldRole .")
        inserts.append(f'<{tessera_uri}> <{VALOR_NS}factorRole> "{_escape(role)}" .')
        optionals.append(f"OPTIONAL {{ <{tessera_uri}> <{VALOR_NS}factorRole> ?oldRole }}")

    if description is not None:
        deletes.append(f"<{tessera_uri}> <{VALOR_NS}description> ?oldDesc .")
        inserts.append(f'<{tessera_uri}> <{VALOR_NS}description> "{_escape(description)}"@nl .')
        optionals.append(f"OPTIONAL {{ <{tessera_uri}> <{VALOR_NS}description> ?oldDesc }}")

    if not deletes:
        return

    sparql = f"""DELETE {{
  GRAPH <{baseline_graph}> {{
    {" ".join(deletes)}
  }}
}}
INSERT {{
  GRAPH <{baseline_graph}> {{
    {" ".join(inserts)}
  }}
}}
WHERE {{
  GRAPH <{baseline_graph}> {{
    <{tessera_uri}> a <{VALOR_NS}Tessera> .
    {" ".join(optionals)}
  }}
}}"""
    await sparql_update(sparql, ds_id)


async def delete_factor_fuseki(tessera_id: str, ds_id: str) -> None:
    """Verwijdert een Factor-Tessera volledig uit de baseline-graph."""
    tessera_uri = _tessera_uri(tessera_id)
    baseline_graph = _ds_baseline_graph(ds_id)
    sparql = f"""DELETE {{
  GRAPH <{baseline_graph}> {{ <{tessera_uri}> ?p ?o . }}
}}
WHERE {{
  GRAPH <{baseline_graph}> {{ <{tessera_uri}> ?p ?o . }}
}}"""
    await sparql_update(sparql, ds_id)


# ---------------------------------------------------------------------------
# Claim reads (SPARQL)
# ---------------------------------------------------------------------------

async def _sparql_get_claims(ds_id: str) -> list[dict]:
    baseline_graph = _ds_baseline_graph(ds_id)
    rows = await sparql_select_global(f"""
SELECT ?tessera ?baseId ?statement ?polarity ?confidence
       ?fromFactor ?sourceBaseId ?toFactor ?targetBaseId
       ?evidenceText ?claimedAt WHERE {{
  GRAPH <{baseline_graph}> {{
    ?tessera a <{VALOR_NS}Tessera> ;
             <{VALOR_NS}baseId> ?baseId ;
             <{VALOR_NS}claimContent> ?statement ;
             <{VALOR_NS}fromFactor> ?fromFactor ;
             <{VALOR_NS}toFactor> ?toFactor .
    ?fromFactor <{VALOR_NS}baseId> ?sourceBaseId .
    ?toFactor   <{VALOR_NS}baseId> ?targetBaseId .
    OPTIONAL {{ ?tessera <{VALOR_NS}polarity>     ?polarity }}
    OPTIONAL {{ ?tessera <{VALOR_NS}confidence>   ?confidence }}
    OPTIONAL {{ ?tessera <{VALOR_NS}evidenceText> ?evidenceText }}
    OPTIONAL {{ ?tessera <{VALOR_NS}claimedAt>    ?claimedAt }}
  }}
}}
""")
    return [
        {
            "id": row["baseId"],
            "version_id": row["baseId"],
            "statement": row.get("statement", ""),
            "polarity": row.get("polarity", "+"),
            "confidence": float(row["confidence"]) if row.get("confidence") else 0.5,
            "evidence_text": row.get("evidenceText"),
            "evidence_url": None,
            "source_id": row["sourceBaseId"],
            "target_id": row["targetBaseId"],
            "source_version_id": row["sourceBaseId"],
            "target_version_id": row["targetBaseId"],
            "claim_thread_id": None,
            "source_thread_id": None,
            "target_thread_id": None,
            "created_at": row.get("claimedAt"),
            "created_by": None,
            "status": None,
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Claim writes (SPARQL)
# ---------------------------------------------------------------------------

async def create_claim_fuseki(
    ds_id: str,
    source_id: str,
    target_id: str,
    statement: str,
    polarity: str,
    user_id: str,
    confidence: float = 1.0,
    evidence_text: Optional[str] = None,
    evidence_url: Optional[str] = None,
) -> str:
    """Maakt een nieuwe Claim-Tessera aan in Fuseki.

    source_id en target_id zijn base_ids van de factor-Tesserae.
    De werkelijke Tessera-URI's worden opgezocht via valor:baseId in de baseline-graph,
    zodat zowel gemigreerde als nieuwe factors correct worden gerefereerd.
    """
    base_id = str(uuid.uuid4())
    tessera_uri = _tessera_uri(base_id)
    baseline_graph = _ds_baseline_graph(ds_id)
    user_uri = f"urn:valor:user:{user_id}"
    claimed_at = datetime.now(timezone.utc).isoformat()
    proposed_uri = f"{VALOR_NS}ProposedStatus"

    # Zoek de werkelijke tessera-URIs op via valor:baseId
    source_uri = await _find_tessera_uri_by_base_id(ds_id, source_id)
    target_uri = await _find_tessera_uri_by_base_id(ds_id, target_id)

    evidence_triple = (
        f'<{tessera_uri}> <{VALOR_NS}evidenceText> "{_escape(evidence_text)}"@nl .'
        if evidence_text else ""
    )

    sparql = f"""INSERT DATA {{
  GRAPH <{baseline_graph}> {{
    <{tessera_uri}> a <{VALOR_NS}Tessera> ;
      <{VALOR_NS}baseId> "{base_id}" ;
      <{VALOR_NS}claimContent> "{_escape(statement)}"@nl ;
      <{VALOR_NS}fromFactor> <{source_uri}> ;
      <{VALOR_NS}toFactor> <{target_uri}> ;
      <{VALOR_NS}polarity> "{_escape(polarity)}" ;
      <{VALOR_NS}confidence> "{confidence}"^^<{_XSD}double> ;
      <{VALOR_NS}epistemicStatus> <{proposed_uri}> ;
      <{VALOR_NS}claimedBy> <{user_uri}> ;
      <{VALOR_NS}claimedAt> "{claimed_at}"^^<{_XSD}dateTime> ;
      <{VALOR_NS}inDesignSpace> <urn:valor:ds:{ds_id}> .
    {evidence_triple}
  }}
}}"""
    await sparql_update(sparql, ds_id)
    return base_id


async def update_claim_fuseki(
    tessera_id: str,
    ds_id: str,
    statement: Optional[str] = None,
    polarity: Optional[str] = None,
    confidence: Optional[float] = None,
    evidence_text: Optional[str] = None,
) -> None:
    """Werkt een bestaande Claim-Tessera bij in Fuseki (alleen opgegeven velden)."""
    tessera_uri = _tessera_uri(tessera_id)
    baseline_graph = _ds_baseline_graph(ds_id)

    deletes, inserts, optionals = [], [], []

    if statement is not None:
        deletes.append(f"<{tessera_uri}> <{VALOR_NS}claimContent> ?oldStmt .")
        inserts.append(f'<{tessera_uri}> <{VALOR_NS}claimContent> "{_escape(statement)}"@nl .')
        optionals.append(f"OPTIONAL {{ <{tessera_uri}> <{VALOR_NS}claimContent> ?oldStmt }}")

    if polarity is not None:
        deletes.append(f"<{tessera_uri}> <{VALOR_NS}polarity> ?oldPol .")
        inserts.append(f'<{tessera_uri}> <{VALOR_NS}polarity> "{_escape(polarity)}" .')
        optionals.append(f"OPTIONAL {{ <{tessera_uri}> <{VALOR_NS}polarity> ?oldPol }}")

    if confidence is not None:
        deletes.append(f"<{tessera_uri}> <{VALOR_NS}confidence> ?oldConf .")
        inserts.append(f'<{tessera_uri}> <{VALOR_NS}confidence> "{confidence}"^^<{_XSD}double> .')
        optionals.append(f"OPTIONAL {{ <{tessera_uri}> <{VALOR_NS}confidence> ?oldConf }}")

    if evidence_text is not None:
        deletes.append(f"<{tessera_uri}> <{VALOR_NS}evidenceText> ?oldEvid .")
        inserts.append(f'<{tessera_uri}> <{VALOR_NS}evidenceText> "{_escape(evidence_text)}"@nl .')
        optionals.append(f"OPTIONAL {{ <{tessera_uri}> <{VALOR_NS}evidenceText> ?oldEvid }}")

    if not deletes:
        return

    sparql = f"""DELETE {{
  GRAPH <{baseline_graph}> {{ {" ".join(deletes)} }}
}}
INSERT {{
  GRAPH <{baseline_graph}> {{ {" ".join(inserts)} }}
}}
WHERE {{
  GRAPH <{baseline_graph}> {{
    <{tessera_uri}> a <{VALOR_NS}Tessera> .
    {" ".join(optionals)}
  }}
}}"""
    await sparql_update(sparql, ds_id)


async def delete_claim_fuseki(tessera_id: str, ds_id: str) -> None:
    """Verwijdert een Claim-Tessera volledig uit de baseline-graph."""
    tessera_uri = _tessera_uri(tessera_id)
    baseline_graph = _ds_baseline_graph(ds_id)
    sparql = f"""DELETE {{
  GRAPH <{baseline_graph}> {{ <{tessera_uri}> ?p ?o . }}
}}
WHERE {{
  GRAPH <{baseline_graph}> {{ <{tessera_uri}> ?p ?o . }}
}}"""
    await sparql_update(sparql, ds_id)
