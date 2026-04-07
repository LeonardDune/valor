"""SOCIA rolpatroon — named graph datalaag (US-AI.5/AI.6).

Implementeert het cross-perspectief rolpatroon waarbij een agent-URI
via context-specifieke triples in de DesignSpace-graph een rol aanneemt.

Architectuur:
  urn:valor:entities              — rigide Kinds (PhysicalAgent, InstitutionalAgent, …)
  urn:valor:ds:{ds_id}/baseline   — socia:playsRole assignaties per DesignSpace

Patroon in baseline-graph:
  <entity_uri> socia:playsRole <role_uri> ;
               socia:isStakeholderIn <ds_uri> ;
               valor:inDesignSpace <ds_uri> .

Migratie (US-AI.6):
  migrate_legacy_socia_actors() migreert urn:valor:socia:actor:{uuid} resources
  naar urn:valor:entities entries. Idempotent en veilig bij lege dataset.
"""
import logging
import uuid as _uuid_mod
from datetime import datetime, timezone

from app.ontology import VALOR_NS
from app.services.fuseki import sparql_select_global, sparql_update, record_provenance_activity

logger = logging.getLogger(__name__)

_SOCIA_NS = f"{VALOR_NS}socia#"
_NEXUS_NS = "https://valor-ecosystem.nl/ontology/nexus#"
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
# Stakeholderkaart ophalen (US-6.1)
# ---------------------------------------------------------------------------

async def get_stakeholder_map(ds_id: str) -> dict:
    """Haalt actoren en socia:IntentionalDependency-edges op uit de DesignSpace-baseline-graph.

    Retourneert:
      {
        "actors": [{"uri": str, "label": str, "entity_type": str, "role_uri": str|None, "role_label_nl": str|None}],
        "dependencies": [{"from_uri": str, "to_uri": str, "dependency_type": str, "dependency_label_nl": str}]
      }
    """
    baseline = _baseline_graph(ds_id)
    _RDFS = "http://www.w3.org/2000/01/rdf-schema#"

    # Actoren: alle entiteiten met socia:isStakeholderIn in de baseline-graph
    actor_rows = await sparql_select_global(f"""
        PREFIX socia:  <{_SOCIA_NS}>
        PREFIX valor:  <{VALOR_NS}>
        PREFIX rdfs:   <{_RDFS}>
        PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

        SELECT DISTINCT ?entity ?entityLabel ?entityType ?role ?roleLabel WHERE {{
          GRAPH <{baseline}> {{
            ?entity socia:isStakeholderIn <{_ds_uri(ds_id)}> .
            OPTIONAL {{ ?entity socia:playsRole ?role . }}
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

    # Dedupliceer op entity URI — SPARQL geeft meerdere rijen per actor
    # bij meerdere rdf:type of socia:playsRole triples.
    seen: dict[str, dict] = {}
    for row in actor_rows:
        uri = row["entity"]
        if uri in seen:
            # Vul ontbrekende velden aan als de latere rij betere data heeft
            existing = seen[uri]
            if not existing.get("entityLabel") and row.get("entityLabel"):
                existing["entityLabel"] = row["entityLabel"]
            if not existing.get("entityType") and row.get("entityType"):
                existing["entityType"] = row["entityType"]
            if not existing.get("role") and row.get("role"):
                existing["role"] = row["role"]
                existing["roleLabel"] = row.get("roleLabel")
        else:
            seen[uri] = dict(row)

    actors = [
        {
            "uri": uri,
            "label": row.get("entityLabel") or uri.split(":")[-1],
            "entity_type": row.get("entityType", ""),
            "entity_type_local": _local_name(row.get("entityType", "")),
            "role_uri": row.get("role"),
            "role_label_nl": row.get("roleLabel"),
        }
        for uri, row in seen.items()
    ]

    # IntentionalDependency-edges
    dep_rows = await sparql_select_global(f"""
        PREFIX socia:  <{_SOCIA_NS}>
        PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?from ?to ?depType ?depLabel WHERE {{
          GRAPH <{baseline}> {{
            ?dep a socia:IntentionalDependency ;
                 socia:dependsOn ?to ;
                 socia:dependedUponBy ?from .
            OPTIONAL {{ ?dep socia:dependencyType ?depType . }}
          }}
          OPTIONAL {{
            GRAPH <{VALOR_NS}socia> {{
              ?depType rdfs:label ?depLabel . FILTER(lang(?depLabel) = "nl")
            }}
          }}
        }}
    """)

    dependencies = [
        {
            "from_uri": row["from"],
            "to_uri": row["to"],
            "dependency_type": row.get("depType", f"{_SOCIA_NS}IntentionalDependency"),
            "dependency_type_local": _local_name(row.get("depType", "IntentionalDependency")),
            "dependency_label_nl": row.get("depLabel") or _local_name(row.get("depType", "afhankelijkheid")),
        }
        for row in dep_rows
    ]

    return {"actors": actors, "dependencies": dependencies}


# ---------------------------------------------------------------------------
# Actor aanmaken (US-6.1 — canvas write-path)
# ---------------------------------------------------------------------------

async def create_actor(
    ds_id: str,
    label: str,
    actor_type_uri: str,
    user_id: str,
) -> dict:
    """Registreert een nieuwe actor in de entities-graph en markeert hem als
    stakeholder in de DesignSpace (socia:isStakeholderIn in baseline-graph).

    actor_type_uri: een volledige URI uit de VALOR-O SOCIA-ontologie,
    bijv. 'https://valor-ecosystem.nl/ontology/socia#HumanStakeholder'.

    Retourneert de aangemaakte actor-gegevens.
    """
    actor_id = str(_uuid_mod.uuid4())
    actor_uri = f"urn:valor:actor:{actor_id}"
    user_uri = f"urn:valor:user:{user_id}"
    created_at = datetime.now(timezone.utc).isoformat()
    baseline = _baseline_graph(ds_id)
    ds_uri = _ds_uri(ds_id)

    escaped_label = _escape(label)

    # Stap 1: label opslaan in entities-graph
    update_entities = f"""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

INSERT DATA {{
  GRAPH <{_ENTITIES_GRAPH}> {{
    <{actor_uri}> a <{actor_type_uri}> ;
      rdfs:label "{escaped_label}"@nl .
  }}
}}"""

    await sparql_update(update_entities, ds_id)

    # Stap 2: isStakeholderIn registreren in baseline-graph
    update_baseline = f"""PREFIX socia: <{_SOCIA_NS}>
PREFIX valor: <{VALOR_NS}>
PREFIX xsd:   <http://www.w3.org/2001/XMLSchema#>

INSERT DATA {{
  GRAPH <{baseline}> {{
    <{actor_uri}> socia:isStakeholderIn <{ds_uri}> ;
      valor:inDesignSpace <{ds_uri}> ;
      valor:claimedBy <{user_uri}> ;
      valor:claimedAt "{created_at}"^^xsd:dateTime .
  }}
}}"""

    await sparql_update(update_baseline, ds_id)

    await record_provenance_activity(
        ds_id,
        "ActorCreated",
        user_uri,
        generated=actor_uri,
    )

    logger.info("[fuseki-socia] Actor aangemaakt: %s (%s) in %s door %s", actor_uri, actor_type_uri, ds_id, user_id)

    return {
        "actor_id": actor_id,
        "actor_uri": actor_uri,
        "label": label,
        "actor_type_uri": actor_type_uri,
        "claimed_by": user_id,
        "claimed_at": created_at,
        "design_space_id": ds_id,
    }


# ---------------------------------------------------------------------------
# Actor bijwerken + verwijderen
# ---------------------------------------------------------------------------

async def update_actor(
    ds_id: str,
    actor_uri: str,
    label: str | None = None,
    actor_type_uri: str | None = None,
) -> dict:
    """Overschrijft het rdfs:label en/of rdf:type van een actor in de entities-graph."""
    if label is None and actor_type_uri is None:
        raise ValueError("Minimaal label of actor_type_uri is vereist.")

    delete_parts = []
    insert_parts = []

    if label is not None:
        escaped_label = _escape(label)
        delete_parts.append(f"    <{actor_uri}> rdfs:label ?oldLabel .")
        insert_parts.append(f'    <{actor_uri}> rdfs:label "{escaped_label}"@nl .')

    if actor_type_uri is not None:
        delete_parts.append(f"    <{actor_uri}> rdf:type ?oldType .")
        insert_parts.append(f"    <{actor_uri}> rdf:type <{actor_type_uri}> .")

    sparql = f"""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

DELETE {{
  GRAPH <{_ENTITIES_GRAPH}> {{
{chr(10).join(delete_parts)}
  }}
}}
INSERT {{
  GRAPH <{_ENTITIES_GRAPH}> {{
{chr(10).join(insert_parts)}
  }}
}}
WHERE {{
  GRAPH <{_ENTITIES_GRAPH}> {{
    OPTIONAL {{ <{actor_uri}> rdfs:label ?oldLabel . }}
    OPTIONAL {{ <{actor_uri}> rdf:type ?oldType . }}
  }}
}}"""

    await sparql_update(sparql, ds_id)

    logger.info("[fuseki-socia] Actor bijgewerkt: %s in %s", actor_uri, ds_id)

    return {"actor_uri": actor_uri, "label": label, "actor_type_uri": actor_type_uri}


async def delete_actor(ds_id: str, actor_uri: str) -> None:
    """Verwijdert een actor uit de entities-graph en de baseline-graph van de DesignSpace."""
    baseline = _baseline_graph(ds_id)

    # Verwijder uit entities-graph
    sparql_entities = f"""DELETE WHERE {{
  GRAPH <{_ENTITIES_GRAPH}> {{
    <{actor_uri}> ?p ?o .
  }}
}}"""
    await sparql_update(sparql_entities, ds_id)

    # Verwijder isStakeholderIn + inDesignSpace triples uit baseline
    sparql_baseline = f"""DELETE WHERE {{
  GRAPH <{baseline}> {{
    <{actor_uri}> ?p ?o .
  }}
}}"""
    await sparql_update(sparql_baseline, ds_id)

    logger.info("[fuseki-socia] Actor verwijderd: %s uit %s", actor_uri, ds_id)


# ---------------------------------------------------------------------------
# StakeholderClaim aanmaken (US-6.2)
# ---------------------------------------------------------------------------

_XSD_NS = "http://www.w3.org/2001/XMLSchema#"


async def create_stakeholder_claim(
    ds_id: str,
    claim_type_uri: str,
    claim_content: str,
    actor_uri: str,
    user_id: str,
) -> dict:
    """Schrijft een socia:StakeholderClaim-subklasse als valor:Tessera.

    claim_type_uri: volledige URI uit de VALOR-O SOCIA-ontologie,
    bijv. 'https://valor-ecosystem.nl/ontology/socia#InterestClaim'.

    Opgeslagen in urn:valor:ds:{ds_id}/agents (AgentTesserae-graph).
    Retourneert een dict met de aangemaakte claim-gegevens.
    """

    tessera_id = str(_uuid_mod.uuid4())
    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    user_uri = f"urn:valor:user:{user_id}"
    claimed_at = datetime.now(timezone.utc).isoformat()

    # StakeholderClaims gaan in de agents-graph van de DesignSpace
    graph_uri = f"urn:valor:ds:{ds_id}/agents"

    escaped_content = _escape(claim_content)

    # epistemicStatus = Proposed (harde waarde — ontologie-onafhankelijk conform Tessera-patroon)
    proposed_uri = f"{VALOR_NS}ProposedStatus"

    update = f"""PREFIX valor: <{VALOR_NS}>
PREFIX socia:  <{_SOCIA_NS}>
PREFIX xsd:    <{_XSD_NS}>

INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> a <{claim_type_uri}> ;
                   a valor:Tessera ;
      valor:claimContent "{escaped_content}"@nl ;
      valor:epistemicStatus <{proposed_uri}> ;
      valor:claimedBy <{user_uri}> ;
      valor:claimedAt "{claimed_at}"^^xsd:dateTime ;
      valor:inDesignSpace <urn:valor:ds:{ds_id}> ;
      socia:claimOf <{actor_uri}> .
  }}
}}"""

    await sparql_update(update, ds_id)

    await record_provenance_activity(
        ds_id,
        "StakeholderClaimCreated",
        user_uri,
        generated=tessera_uri,
    )

    logger.info(
        "[fuseki-socia] StakeholderClaim aangemaakt: %s (%s) in %s door %s",
        tessera_uri, claim_type_uri, ds_id, user_id,
    )

    return {
        "tessera_id": tessera_id,
        "tessera_uri": tessera_uri,
        "claim_type_uri": claim_type_uri,
        "claim_content": claim_content,
        "epistemic_status": "Proposed",
        "actor_uri": actor_uri,
        "claimed_by": user_id,
        "claimed_at": claimed_at,
        "design_space_id": ds_id,
    }


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


# ---------------------------------------------------------------------------
# EcosystemAgent aanmaken (US-6.4)
# ---------------------------------------------------------------------------

async def create_ecosystem_agent(
    ds_id: str,
    label: str,
    commitment_duration_uri: str,
    member_agent_uris: list[str],
    user_id: str,
) -> dict:
    """Registreert een nexus:EcosystemAgent met nexus:CollaborationCommitment in Fuseki.

    commitment_duration_uri: volledige URI uit de VALOR-O NEXUS-ontologie.

    Opgeslagen in urn:valor:ds:{ds_id}/agents (AgentTesserae-graph).
    De EcosystemAgent is een subklasse van socia:Actor.
    """
    agent_id = str(_uuid_mod.uuid4())
    agent_uri = f"urn:valor:nexus:agent:{agent_id}"
    commitment_uri = f"urn:valor:nexus:commitment:{agent_id}"
    user_uri = f"urn:valor:user:{user_id}"
    created_at = datetime.now(timezone.utc).isoformat()

    graph_uri = f"urn:valor:ds:{ds_id}/agents"
    escaped_label = _escape(label)

    member_triples = "\n".join(
        f"    <{agent_uri}> <{_NEXUS_NS}hasMember> <{uri}> ."
        for uri in member_agent_uris
    )

    update = f"""PREFIX nexus: <{_NEXUS_NS}>
PREFIX socia: <{_SOCIA_NS}>
PREFIX valor: <{VALOR_NS}>
PREFIX rdfs:  <{_RDFS_LABEL.rsplit('#', 1)[0]}#>
PREFIX xsd:   <{_XSD_NS}>

INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{agent_uri}> a nexus:EcosystemAgent ;
                  a socia:Actor ;
      rdfs:label "{escaped_label}" ;
      nexus:hasCommitment <{commitment_uri}> ;
      valor:inDesignSpace <urn:valor:ds:{ds_id}> ;
      valor:claimedBy <{user_uri}> ;
      valor:claimedAt "{created_at}"^^xsd:dateTime .
    <{commitment_uri}> a nexus:CollaborationCommitment ;
      nexus:commitmentDuration <{commitment_duration_uri}> .
{member_triples}
  }}
}}"""

    await sparql_update(update, ds_id)

    await record_provenance_activity(
        ds_id,
        "EcosystemAgentCreated",
        user_uri,
        generated=agent_uri,
    )

    logger.info(
        "[fuseki-socia] EcosystemAgent aangemaakt: %s (%s) in %s door %s",
        agent_uri, commitment_duration_uri, ds_id, user_id,
    )

    return {
        "agent_id": agent_id,
        "agent_uri": agent_uri,
        "label": label,
        "commitment_uri": commitment_uri,
        "commitment_duration_uri": commitment_duration_uri,
        "member_agent_uris": member_agent_uris,
        "created_by": user_id,
        "created_at": created_at,
        "design_space_id": ds_id,
    }


async def get_ecosystem_agents(ds_id: str) -> list[dict]:
    """Haalt alle nexus:EcosystemAgents op met CollaborationCondition-status.

    Status = "Volledig" | "Gedeeltelijk" | "Onvolledig" op basis van:
      - commit aanwezig (nexus:hasCommitment)
      - architectuur aanwezig (nexus:hasArchitecture — optioneel triple)
      - dispositionele config aanwezig (nexus:hasDispositionConfig — optioneel triple)
    """
    graph_uri = f"urn:valor:ds:{ds_id}/agents"

    rows = await sparql_select_global(f"""
        PREFIX nexus: <{_NEXUS_NS}>
        PREFIX socia: <{_SOCIA_NS}>
        PREFIX rdfs:  <{_RDFS_LABEL.rsplit('#', 1)[0]}#>
        PREFIX xsd:   <{_XSD_NS}>

        SELECT ?agent ?label ?commitment ?commitmentDuration
               (BOUND(?arch) AS ?hasArchitecture)
               (BOUND(?dispConf) AS ?hasDispositionConfig)
        WHERE {{
          GRAPH <{graph_uri}> {{
            ?agent a <{_NEXUS_NS}EcosystemAgent> .
            OPTIONAL {{ ?agent rdfs:label ?label . }}
            OPTIONAL {{
              ?agent <{_NEXUS_NS}hasCommitment> ?commitment .
              OPTIONAL {{ ?commitment <{_NEXUS_NS}commitmentDuration> ?commitmentDuration . }}
            }}
            OPTIONAL {{ ?agent <{_NEXUS_NS}hasArchitecture> ?arch . }}
            OPTIONAL {{ ?agent <{_NEXUS_NS}hasDispositionConfig> ?dispConf . }}
          }}
        }}
    """)

    # Per agent de leden ophalen
    member_rows = await sparql_select_global(f"""
        PREFIX nexus: <{_NEXUS_NS}>

        SELECT ?agent ?member WHERE {{
          GRAPH <{graph_uri}> {{
            ?agent a <{_NEXUS_NS}EcosystemAgent> ;
                   <{_NEXUS_NS}hasMember> ?member .
          }}
        }}
    """)

    members_by_agent: dict[str, list[str]] = {}
    for row in member_rows:
        agent_uri = row["agent"]
        members_by_agent.setdefault(agent_uri, []).append(row["member"])

    result = []
    for row in rows:
        agent_uri = row["agent"]
        has_commit = row.get("commitment") is not None
        has_arch = str(row.get("hasArchitecture", "false")).lower() == "true"
        has_disp = str(row.get("hasDispositionConfig", "false")).lower() == "true"

        layers_present = sum([has_commit, has_arch, has_disp])
        if layers_present == 3:
            condition_status = "Volledig"
        elif layers_present >= 1:
            condition_status = "Gedeeltelijk"
        else:
            condition_status = "Onvolledig"

        result.append({
            "agent_uri": agent_uri,
            "label": row.get("label", agent_uri.split(":")[-1]),
            "commitment_uri": row.get("commitment"),
            "commitment_duration": row.get("commitmentDuration"),
            "member_agent_uris": members_by_agent.get(agent_uri, []),
            "condition_status": condition_status,
            "condition_layers": {
                "commitment": has_commit,
                "architecture": has_arch,
                "disposition_config": has_disp,
            },
        })

    return result


# ---------------------------------------------------------------------------
# StakeholderGroepen (US-6.5)
# ---------------------------------------------------------------------------

_DEMOS_NS = "https://valor-ecosystem.nl/ontology/demos#"


async def create_stakeholder_group(
    ds_id: str,
    label: str,
    interest_level_uri: str,
    represented_by_uri: str | None,
    user_id: str,
) -> dict:
    """Registreert een socia:StakeholderGroup met demos:interestLevel in Fuseki.

    interest_level_uri: volledige URI uit de VALOR-O DEMOS-ontologie.

    Opgeslagen in urn:valor:ds:{ds_id}/baseline.
    """
    group_id = str(_uuid_mod.uuid4())
    group_uri = f"urn:valor:socia:group:{group_id}"
    user_uri = f"urn:valor:user:{user_id}"
    created_at = datetime.now(timezone.utc).isoformat()
    escaped_label = _escape(label)
    baseline = _baseline_graph(ds_id)

    represented_triple = (
        f'    <{group_uri}> <{_DEMOS_NS}representedBy> <{represented_by_uri}> .'
        if represented_by_uri
        else ""
    )

    update = f"""PREFIX socia: <{_SOCIA_NS}>
PREFIX demos: <{_DEMOS_NS}>
PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
PREFIX valor: <{VALOR_NS}>
PREFIX xsd:   <{_XSD_NS}>

INSERT DATA {{
  GRAPH <{baseline}> {{
    <{group_uri}> a <{_SOCIA_NS}StakeholderGroup> ;
      rdfs:label "{escaped_label}" ;
      <{_DEMOS_NS}interestLevel> <{interest_level_uri}> ;
      valor:inDesignSpace <{_ds_uri(ds_id)}> ;
      valor:claimedBy <{user_uri}> ;
      valor:claimedAt "{created_at}"^^xsd:dateTime .
{represented_triple}
  }}
}}"""

    await sparql_update(update, ds_id)

    await record_provenance_activity(
        ds_id,
        "StakeholderGroupCreated",
        user_uri,
        generated=group_uri,
    )

    logger.info(
        "[fuseki-socia] StakeholderGroup aangemaakt: %s (%s) in %s door %s",
        group_uri, interest_level_uri, ds_id, user_id,
    )

    return {
        "group_id": group_id,
        "group_uri": group_uri,
        "label": label,
        "interest_level_uri": interest_level_uri,
        "represented_by_uri": represented_by_uri,
        "is_represented": represented_by_uri is not None,
        "created_by": user_id,
        "created_at": created_at,
        "design_space_id": ds_id,
    }


async def get_stakeholder_groups(ds_id: str) -> list[dict]:
    """Haalt alle socia:StakeholderGroups op uit de baseline-graph van een DesignSpace.

    Retourneert per groep ook of er een demos:representedBy aanwezig is (is_represented).
    """
    baseline = _baseline_graph(ds_id)

    rows = await sparql_select_global(f"""
        PREFIX socia:  <{_SOCIA_NS}>
        PREFIX demos:  <{_DEMOS_NS}>
        PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?group ?label ?interestLevel (BOUND(?rep) AS ?isRepresented) ?rep WHERE {{
          GRAPH <{baseline}> {{
            ?group a <{_SOCIA_NS}StakeholderGroup> ;
                   rdfs:label ?label ;
                   <{_DEMOS_NS}interestLevel> ?interestLevel .
            OPTIONAL {{ ?group <{_DEMOS_NS}representedBy> ?rep . }}
          }}
        }}
    """)

    return [
        {
            "group_uri": row["group"],
            "label": row.get("label", row["group"].split(":")[-1]),
            "interest_level": row.get("interestLevel", ""),
            "is_represented": str(row.get("isRepresented", "false")).lower() == "true",
            "represented_by_uri": row.get("rep"),
        }
        for row in rows
    ]


async def get_high_interest_groups(ds_id: str) -> list[dict]:
    """Filtert socia:StakeholderGroups op interestLevel = 'High' met representatiestatus.

    Bedoeld voor DEMOS InclusivityCoverage-berekening.
    """
    baseline = _baseline_graph(ds_id)

    rows = await sparql_select_global(f"""
        PREFIX socia:  <{_SOCIA_NS}>
        PREFIX demos:  <{_DEMOS_NS}>
        PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?group ?label (BOUND(?rep) AS ?isRepresented) ?rep WHERE {{
          GRAPH <{baseline}> {{
            ?group a <{_SOCIA_NS}StakeholderGroup> ;
                   rdfs:label ?label ;
                   <{_DEMOS_NS}interestLevel> "High" .
            OPTIONAL {{ ?group <{_DEMOS_NS}representedBy> ?rep . }}
          }}
        }}
    """)

    return [
        {
            "group_uri": row["group"],
            "label": row.get("label", row["group"].split(":")[-1]),
            "interest_level": "High",
            "is_represented": str(row.get("isRepresented", "false")).lower() == "true",
            "represented_by_uri": row.get("rep"),
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Migratie: legacy socia:Actor → Entity Registry (US-AI.6)
# ---------------------------------------------------------------------------

_LEGACY_ACTOR_TYPE = f"{_SOCIA_NS}Actor"
_LEGACY_ACTOR_URI_PREFIX = "urn:valor:socia:actor:"
_ENTITIES_GRAPH = "urn:valor:entities"


async def migrate_legacy_socia_actors() -> dict:
    """Migreert legacy socia:Actor-resources naar het Entity Registry patroon.

    Per gevonden actor:
      1. Bepaalt het entity type (PhysicalAgent / InstitutionalAgent) op basis van socia:actorType
      2. Maakt / hergebruikt een urn:valor:entities:... URI
      3. Schrijft socia:playsRole naar de DesignSpace-baseline-graph
      4. Herschrijft valor:claimedBy op Tesserae naar de nieuwe entity URI

    Idempotent: als een actor al gemigreerd is (entity URI bestaat al), wordt hij overgeslagen.
    Retourneert een dict met migratie-statistieken.
    """
    from app.ontology import UFOC_NS
    import uuid as _uuid

    stats = {"found": 0, "migrated": 0, "skipped": 0, "errors": []}

    # 1. Zoek alle legacy actors over alle named graphs
    legacy_rows = await sparql_select_global(f"""
        PREFIX socia: <{_SOCIA_NS}>
        PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX valor: <{VALOR_NS}>

        SELECT ?actor ?graph ?actorType ?actorRole ?label WHERE {{
          GRAPH ?graph {{
            ?actor a <{_LEGACY_ACTOR_TYPE}> .
            OPTIONAL {{ ?actor socia:actorType ?actorType . }}
            OPTIONAL {{ ?actor socia:actorRole ?actorRole . }}
            OPTIONAL {{ ?actor rdfs:label ?label . }}
            OPTIONAL {{ ?actor valor:claimContent ?label . }}
          }}
          FILTER(STRSTARTS(STR(?actor), "{_LEGACY_ACTOR_URI_PREFIX}"))
        }}
    """)

    stats["found"] = len(legacy_rows)
    if not legacy_rows:
        logger.info("[socia-migrate] Geen legacy actors gevonden — niets te migreren.")
        return stats

    # 2. Controleer welke al gemigreerd zijn (entity URI bestaat al in registry)
    migrated_map: dict[str, str] = {}  # legacy_uri → entity_uri
    for row in legacy_rows:
        legacy_uri = row["actor"]
        graph = row.get("graph", "")
        ds_id = graph.replace("urn:valor:ds:", "").split("/")[0] if "urn:valor:ds:" in graph else None

        # Bepaal entity type
        actor_type_str = row.get("actorType", "IndividualAgent")
        if "Institutional" in actor_type_str or "Organisation" in actor_type_str:
            entity_type_class = f"{UFOC_NS}InstitutionalAgent"
            entity_uri_prefix = f"{_ENTITIES_GRAPH}:org"
        else:
            entity_type_class = f"{UFOC_NS}PhysicalAgent"
            entity_uri_prefix = f"{_ENTITIES_GRAPH}:person"

        # Hergebruik bestaande mapping of genereer nieuwe UUID
        if legacy_uri not in migrated_map:
            # Extraheer de UUID uit de legacy URI
            legacy_id = legacy_uri.replace(_LEGACY_ACTOR_URI_PREFIX, "")
            entity_uri = f"{entity_uri_prefix}:{legacy_id}"
            migrated_map[legacy_uri] = entity_uri

            # Controleer of entity al bestaat
            existing = await sparql_select_global(f"""
                SELECT ?s WHERE {{
                  GRAPH <{_ENTITIES_GRAPH}> {{
                    <{entity_uri}> a <{entity_type_class}> .
                    BIND(<{entity_uri}> AS ?s)
                  }}
                }} LIMIT 1
            """)
            if existing:
                stats["skipped"] += 1
                continue

            # Schrijf entity naar Entity Registry
            label = _escape(row.get("label", legacy_id))
            insert_entity = f"""
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                INSERT DATA {{
                  GRAPH <{_ENTITIES_GRAPH}> {{
                    <{entity_uri}> a <{entity_type_class}> ;
                                   rdfs:label "{label}" .
                  }}
                }}
            """
            try:
                await sparql_update(insert_entity, "migrate-entity")
            except Exception as exc:
                stats["errors"].append(f"{legacy_uri}: {exc}")
                continue

            # Schrijf playsRole naar DesignSpace-baseline (als ds_id bekend)
            if ds_id:
                role_str = row.get("actorRole", "")
                role_uri = f"{_SOCIA_NS}{role_str.capitalize()}" if role_str else None
                if role_uri:
                    try:
                        await assign_actor_role(entity_uri, role_uri, ds_id)
                    except Exception:
                        pass  # Rol-mapping best-effort

            stats["migrated"] += 1

    # 3. Herschrijf valor:claimedBy op Tesserae (per gemigeerde actor)
    for legacy_uri, entity_uri in migrated_map.items():
        rewrite = f"""
            PREFIX valor: <{VALOR_NS}>
            DELETE {{
              GRAPH ?g {{ ?tessera valor:claimedBy <{legacy_uri}> . }}
            }}
            INSERT {{
              GRAPH ?g {{ ?tessera valor:claimedBy <{entity_uri}> . }}
            }}
            WHERE {{
              GRAPH ?g {{ ?tessera valor:claimedBy <{legacy_uri}> . }}
            }}
        """
        try:
            await sparql_update(rewrite, "migrate-claimedbuy")
        except Exception as exc:
            stats["errors"].append(f"claimedBy rewrite {legacy_uri}: {exc}")

    logger.info("[socia-migrate] Klaar: %s", stats)
    return stats
