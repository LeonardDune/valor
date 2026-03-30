"""Entity Registry — named graph urn:valor:entities.

Implementeert de platformbrede Entity Registry als single source of truth
voor alle rigide Kinds in VALOR (US-AI.3).

Architectuur:
  urn:valor:entities              — alle rigide Kinds (platform-breed, persistent)
  urn:valor:ds:{ds_id}/baseline   — rol-assignaties per perspectief/DesignSpace

URI-conventies:
  urn:valor:entities:person:{supabase_uuid}   — interne gebruikers
  urn:valor:entities:person:{random_uuid}     — externe personen
  urn:valor:entities:org:{random_uuid}        — organisaties
  urn:valor:entities:norm:{slug}              — wetten/regelingen
"""
import logging
import uuid
from typing import Optional

from app.ontology import UFOC_NS, VALOR_NS
from app.services.fuseki import sparql_select_global, sparql_update

logger = logging.getLogger(__name__)

_ENTITIES_GRAPH = "urn:valor:entities"
_RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
_RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"

# Ondersteunde entity types → UFOC klasse-URI
ENTITY_TYPE_MAP = {
    "PhysicalAgent": f"{UFOC_NS}PhysicalAgent",
    "InstitutionalAgent": f"{UFOC_NS}InstitutionalAgent",
    "NormativeDescription": f"{UFOC_NS}NormativeDescription",
    "SocialObject": f"{UFOC_NS}SocialObject",
}

# URI-prefix per entity type
_URI_PREFIX_MAP = {
    "PhysicalAgent": "person",
    "InstitutionalAgent": "org",
    "NormativeDescription": "norm",
    "SocialObject": "obj",
}


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")


def _entity_uri(entity_type: str, identifier: str) -> str:
    prefix = _URI_PREFIX_MAP.get(entity_type, "entity")
    return f"{_ENTITIES_GRAPH}:{prefix}:{identifier}"


# ---------------------------------------------------------------------------
# JIT-bridge: Supabase → Fuseki
# ---------------------------------------------------------------------------

async def ensure_person_entity(supabase_id: str, name: Optional[str] = None) -> str:
    """Garandeert dat een ufoc:PhysicalAgent-resource bestaat voor de Supabase-gebruiker.

    Geeft de URI terug. Maakt JIT aan als nog niet aanwezig.
    URI-patroon: urn:valor:entities:person:{supabase_uuid}
    """
    uri = _entity_uri("PhysicalAgent", supabase_id)

    # Check of entity al bestaat
    rows = await sparql_select_global(
        f"SELECT ?uri WHERE {{ GRAPH <{_ENTITIES_GRAPH}> {{ <{uri}> a <{UFOC_NS}PhysicalAgent> }} }}"
    )
    if rows:
        return uri

    # JIT aanmaken
    label = _escape(name or supabase_id)
    update = f"""
INSERT DATA {{
  GRAPH <{_ENTITIES_GRAPH}> {{
    <{uri}> a <{UFOC_NS}PhysicalAgent> ;
      <{_RDFS_LABEL}> "{label}"@nl ;
      <{VALOR_NS}supabaseId> "{_escape(supabase_id)}" ;
      <{VALOR_NS}entityCreatedAt> "{_now_iso()}"^^<http://www.w3.org/2001/XMLSchema#dateTime> .
  }}
}}
"""
    await sparql_update(update, "entities")
    logger.info("Entity Registry: PhysicalAgent aangemaakt voor Supabase-gebruiker %s", supabase_id)
    return uri


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

async def create_entity(
    entity_type: str,
    label: str,
    properties: Optional[dict] = None,
    identifier: Optional[str] = None,
) -> str:
    """Maakt een nieuwe entiteit aan in urn:valor:entities.

    Geeft de URI terug.
    """
    if entity_type not in ENTITY_TYPE_MAP:
        raise ValueError(f"Onbekend entity type: {entity_type}. Kies uit: {list(ENTITY_TYPE_MAP)}")

    ident = identifier or str(uuid.uuid4())
    uri = _entity_uri(entity_type, ident)
    class_uri = ENTITY_TYPE_MAP[entity_type]
    label_escaped = _escape(label)

    extra_triples = ""
    if properties:
        for key, value in properties.items():
            if value is not None:
                escaped_val = _escape(str(value))
                extra_triples += f'    <{VALOR_NS}{key}> "{escaped_val}" ;\n'

    update = f"""
INSERT DATA {{
  GRAPH <{_ENTITIES_GRAPH}> {{
    <{uri}> a <{class_uri}> ;
      <{_RDFS_LABEL}> "{label_escaped}"@nl ;
      <{VALOR_NS}entityCreatedAt> "{_now_iso()}"^^<http://www.w3.org/2001/XMLSchema#dateTime> ;
{extra_triples}      <{VALOR_NS}entityId> "{_escape(ident)}" .
  }}
}}
"""
    await sparql_update(update, "entities")
    logger.info("Entity Registry: %s aangemaakt met URI %s", entity_type, uri)
    return uri


async def get_entity(uri: str) -> Optional[dict]:
    """Haalt een entiteit op uit de Entity Registry op basis van URI.

    Geeft None terug als de entiteit niet bestaat.
    """
    rows = await sparql_select_global(f"""
SELECT ?type ?label ?supabaseId ?entityId ?createdAt WHERE {{
  GRAPH <{_ENTITIES_GRAPH}> {{
    <{uri}> a ?type ;
      OPTIONAL {{ <{uri}> <{_RDFS_LABEL}> ?label }}
      OPTIONAL {{ <{uri}> <{VALOR_NS}supabaseId> ?supabaseId }}
      OPTIONAL {{ <{uri}> <{VALOR_NS}entityId> ?entityId }}
      OPTIONAL {{ <{uri}> <{VALOR_NS}entityCreatedAt> ?createdAt }}
  }}
}}
""")
    if not rows:
        return None

    row = rows[0]
    # Bepaal entity_type label vanuit URI
    type_uri = row.get("type", "")
    entity_type = next(
        (k for k, v in ENTITY_TYPE_MAP.items() if v == type_uri),
        type_uri,
    )
    return {
        "uri": uri,
        "entity_type": entity_type,
        "label": row.get("label"),
        "supabase_id": row.get("supabaseId"),
        "entity_id": row.get("entityId"),
        "created_at": row.get("createdAt"),
    }


async def search_entities(
    query: str,
    entity_type: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """Zoekt entiteiten in de Entity Registry op basis van label (case-insensitive substring).

    Optionele filter op entity_type.
    """
    type_filter = ""
    if entity_type and entity_type in ENTITY_TYPE_MAP:
        class_uri = ENTITY_TYPE_MAP[entity_type]
        type_filter = f"?uri a <{class_uri}> ."
    else:
        type_filter = f"?uri a ?type ."

    escaped_q = _escape(query.lower())

    sparql = f"""
SELECT ?uri ?type ?label WHERE {{
  GRAPH <{_ENTITIES_GRAPH}> {{
    {type_filter}
    ?uri a ?type .
    OPTIONAL {{ ?uri <{_RDFS_LABEL}> ?label }}
    FILTER (CONTAINS(LCASE(STR(?label)), "{escaped_q}") || CONTAINS(STR(?uri), "{escaped_q}"))
  }}
}}
LIMIT {limit}
"""
    rows = await sparql_select_global(sparql)
    results = []
    for row in rows:
        type_uri = row.get("type", "")
        entity_type_label = next(
            (k for k, v in ENTITY_TYPE_MAP.items() if v == type_uri),
            type_uri,
        )
        results.append({
            "uri": row["uri"],
            "entity_type": entity_type_label,
            "label": row.get("label"),
        })
    return results


# ---------------------------------------------------------------------------
# Rol-assignatie
# ---------------------------------------------------------------------------

async def assign_role(
    entity_uri: str,
    role_uri: str,
    ds_id: str,
    context: Optional[str] = None,
) -> None:
    """Wijst een rol toe aan een entiteit in de baseline-graph van een DesignSpace.

    Triple: entity_uri valor:playsRole role_uri  (in urn:valor:ds:{ds_id}/baseline)
    """
    baseline_graph = f"urn:valor:ds:{ds_id}/baseline"
    context_triple = ""
    if context:
        escaped_ctx = _escape(context)
        context_triple = f'    <{VALOR_NS}roleContext> "{escaped_ctx}" ;\n'

    update = f"""
INSERT DATA {{
  GRAPH <{baseline_graph}> {{
    <{entity_uri}> <{VALOR_NS}playsRole> <{role_uri}> ;
{context_triple}      <{VALOR_NS}roleAssignedAt> "{_now_iso()}"^^<http://www.w3.org/2001/XMLSchema#dateTime> .
  }}
}}
"""
    await sparql_update(update, ds_id)
    logger.info(
        "Entity Registry: rol %s toegewezen aan %s in DesignSpace %s",
        role_uri, entity_uri, ds_id,
    )


async def get_roles_for_entity(entity_uri: str, ds_id: str) -> list[dict]:
    """Haalt alle rollen op voor een entiteit in een specifieke DesignSpace.

    Leest uit urn:valor:ds:{ds_id}/baseline.
    """
    baseline_graph = f"urn:valor:ds:{ds_id}/baseline"
    rows = await sparql_select_global(f"""
SELECT ?role ?context ?assignedAt WHERE {{
  GRAPH <{baseline_graph}> {{
    <{entity_uri}> <{VALOR_NS}playsRole> ?role .
    OPTIONAL {{ <{entity_uri}> <{VALOR_NS}roleContext> ?context }}
    OPTIONAL {{ <{entity_uri}> <{VALOR_NS}roleAssignedAt> ?assignedAt }}
  }}
}}
""")
    return [
        {
            "role_uri": row["role"],
            "context": row.get("context"),
            "assigned_at": row.get("assignedAt"),
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Backfill helpers
# ---------------------------------------------------------------------------

async def backfill_existing_users(users: list[dict]) -> int:
    """Maakt PhysicalAgent-entities aan voor bestaande gebruikers die nog geen entity hebben.

    Verwacht een lijst van dicts met 'id' (Supabase UUID) en optioneel 'name'.
    Geeft het aantal nieuw aangemaakte entities terug.
    """
    created = 0
    for user in users:
        user_id = user.get("id")
        if not user_id:
            continue
        uri = await ensure_person_entity(user_id, user.get("name"))
        if uri:
            created += 1
    return created


# ---------------------------------------------------------------------------
# Intern
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
