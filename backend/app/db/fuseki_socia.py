"""SOCIA rolpatroon — named graph datalaag (US-AI.5).

Implementeert het cross-perspectief rolpatroon waarbij een agent-URI
via context-specifieke triples in de DesignSpace-graph een rol aanneemt.

Architectuur:
  urn:valor:entities              — rigide Kinds (PhysicalAgent, InstitutionalAgent, …)
  urn:valor:ds:{ds_id}/baseline   — socia:playsRole assignaties per DesignSpace

Patroon in baseline-graph:
  <entity_uri> socia:playsRole <role_uri> ;
               socia:isStakeholderIn <ds_uri> ;
               valor:inDesignSpace <ds_uri> .
"""
import logging

from app.ontology import VALOR_NS
from app.services.fuseki import sparql_select_global, sparql_update

logger = logging.getLogger(__name__)

_SOCIA_NS = f"{VALOR_NS}socia#"
_ENTITIES_GRAPH = "urn:valor:entities"
_RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
_RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"


def _baseline_graph(ds_id: str) -> str:
    return f"urn:valor:ds:{ds_id}/baseline"


def _ds_uri(ds_id: str) -> str:
    return f"urn:valor:ds:{ds_id}"


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")


def _local_name(uri: str) -> str:
    """Haalt het lokale fragment uit een URI (na # of laatste /)."""
    if "#" in uri:
        return uri.split("#")[-1]
    return uri.rstrip("/").split("/")[-1]


# ---------------------------------------------------------------------------
# Rol-assignatie schrijven
# ---------------------------------------------------------------------------

async def assign_actor_role(entity_uri: str, role_uri: str, ds_id: str) -> None:
    """Schrijft een socia:playsRole-assignatie naar de DesignSpace-baseline-graph.

    Idempotent: bij bestaande assignatie wordt niets overschreven (INSERT WHERE NOT EXISTS).
    """
    baseline = _baseline_graph(ds_id)
    ds_uri = _ds_uri(ds_id)

    update = f"""
        PREFIX socia: <{_SOCIA_NS}>
        PREFIX valor: <{VALOR_NS}>

        INSERT {{
          GRAPH <{baseline}> {{
            <{entity_uri}> socia:playsRole <{role_uri}> ;
                           socia:isStakeholderIn <{ds_uri}> ;
                           valor:inDesignSpace <{ds_uri}> .
          }}
        }}
        WHERE {{
          FILTER NOT EXISTS {{
            GRAPH <{baseline}> {{
              <{entity_uri}> socia:playsRole <{role_uri}> .
            }}
          }}
        }}
    """
    await sparql_update(update, "socia-role")
    logger.info("[fuseki-socia] playsRole: %s → %s in %s", entity_uri, role_uri, ds_id)


# ---------------------------------------------------------------------------
# Actor rollen in een DesignSpace ophalen
# ---------------------------------------------------------------------------

async def get_actor_roles_in_ds(ds_id: str) -> list[dict]:
    """Retourneert alle actor-rol-paren in een DesignSpace, verrijkt met Entity Registry data.

    JOIN-t urn:valor:entities voor label en rdf:type van de agent.
    JOIN-t de SOCIA-ontologiegraph voor het Nederlands label van de rol.
    """
    baseline = _baseline_graph(ds_id)

    rows = await sparql_select_global(f"""
        PREFIX socia:  <{_SOCIA_NS}>
        PREFIX valor:  <{VALOR_NS}>
        PREFIX rdfs:   <{_RDFS_LABEL.rsplit('#', 1)[0]}#>
        PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

        SELECT ?entity ?role ?entityLabel ?entityType ?roleLabel WHERE {{
          GRAPH <{baseline}> {{
            ?entity socia:playsRole ?role .
          }}
          OPTIONAL {{
            GRAPH <{_ENTITIES_GRAPH}> {{
              OPTIONAL {{ ?entity rdfs:label ?entityLabel . }}
              OPTIONAL {{ ?entity rdf:type ?entityType . }}
            }}
          }}
          OPTIONAL {{
            GRAPH <{VALOR_NS}socia> {{
              ?role rdfs:label ?roleLabel . FILTER(lang(?roleLabel) = "nl")
            }}
          }}
        }}
    """)

    result = []
    for row in rows:
        entity_uri = row["entity"]
        role_uri = row["role"]
        result.append({
            "entity_uri": entity_uri,
            "role_uri": role_uri,
            "entity_label": row.get("entityLabel", entity_uri.split(":")[-1]),
            "entity_type": row.get("entityType", ""),
            "entity_type_local": row.get("entityType", "").split("#")[-1],
            "role_local": role_uri.split("#")[-1],
            "role_label_nl": row.get("roleLabel", role_uri.split("#")[-1]),
        })
    return result


# ---------------------------------------------------------------------------
# Tesserae over een agent ophalen (cross-perspectief)
# ---------------------------------------------------------------------------

async def get_tesserae_for_agent(entity_uri: str, ds_id: str) -> list[dict]:
    """Retourneert alle Tesserae in een DesignSpace waar valor:claimedBy = entity_uri.

    Queryt over alle named graphs van de DesignSpace (baseline + overige).
    """
    ds_prefix = f"urn:valor:ds:{ds_id}"

    rows = await sparql_select_global(f"""
        PREFIX valor: <{VALOR_NS}>
        PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

        SELECT ?tessera ?type ?content ?graph WHERE {{
          GRAPH ?graph {{
            ?tessera valor:claimedBy <{entity_uri}> .
            OPTIONAL {{ ?tessera rdf:type ?type . }}
            OPTIONAL {{ ?tessera valor:claimContent ?content . }}
          }}
          FILTER(STRSTARTS(STR(?graph), "{ds_prefix}/"))
        }}
    """)

    return [
        {
            "tessera_uri": row["tessera"],
            "type": row.get("type", ""),
            "type_local": _local_name(row.get("type", "")),
            "content": row.get("content", ""),
            "graph": row.get("graph", ""),
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# DesignSpaces voor een agent ophalen
# ---------------------------------------------------------------------------

async def get_designspaces_for_agent(entity_uri: str) -> list[str]:
    """Retourneert alle DesignSpace-IDs waar de agent een socia:playsRole heeft."""
    rows = await sparql_select_global(f"""
        PREFIX socia: <{_SOCIA_NS}>

        SELECT DISTINCT ?ds WHERE {{
          GRAPH ?graph {{
            <{entity_uri}> socia:isStakeholderIn ?ds .
          }}
          FILTER(STRSTARTS(STR(?graph), "urn:valor:ds:"))
        }}
    """)

    return [
        row["ds"].replace("urn:valor:ds:", "")
        for row in rows
    ]
