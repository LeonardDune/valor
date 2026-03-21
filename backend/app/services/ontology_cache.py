"""Startup cache van ontologie-gedreven validatiedata uit Fuseki.

Geladen bij applicatie-startup via load_ontology_cache().
Queryt de VALOR-O ontologie-graphs in Fuseki voor:
  - EvidenceType instanties (English label -> URI)
  - EpistemicStatus instanties (English label -> URI)
  - Geldige statusovergangen (valor:allowedTransitionTo)
  - Statussen die een DecisionEpisode vereisen (valor:requiresDecisionEpisode)
  - UncertaintyLevel instanties (PAMS-taxonomie, English label -> URI)
  - disc:ContributionType instanties (Dutch label -> URI)
"""
import logging

from app.ontology import VALOR_NS, VALOR_SITE_BASE
from app.services.fuseki import sparql_select_global

logger = logging.getLogger(__name__)

_TESSERA_GRAPH = f"{VALOR_NS}tessera"
_shacl_shapes_graph = f"{VALOR_SITE_BASE}shacl/tessera"

_evidence_label_to_uri: dict[str, str] = {}
_status_label_to_uri: dict[str, str] = {}
_status_uri_to_label: dict[str, str] = {}
_valid_transitions: dict[str, set[str]] = {}
_requires_decision_episode: set[str] = set()
_argue_label_to_uri: dict[str, str] = {}        # "undermines" → URI
_uncertainty_label_to_uri: dict[str, str] = {}  # "StatisticalRisk" → URI
# Participant roles: label → {uri, rbac_role, weight, voting_right}
_participant_role_data: dict[str, dict] = {}
# RBAC role weights derived from ontology: "admin" → 30
_rbac_role_weights: dict[str, int] = {}
_disc_contribution_type_label_to_uri: dict[str, str] = {}  # "Vraag" → URI
_status_uri_to_nl_label: dict[str, str] = {}  # URI → "Betwist" etc.
_system_situation_uris: set[str] = set()  # sysont:SystemSituation instanties


_DISC_GRAPH = f"{VALOR_NS}disc"


async def load_ontology_cache() -> None:
    global _evidence_label_to_uri, _status_label_to_uri, _status_uri_to_label
    global _valid_transitions, _requires_decision_episode, _argue_label_to_uri
    global _uncertainty_label_to_uri, _participant_role_data, _rbac_role_weights
    global _disc_contribution_type_label_to_uri, _status_uri_to_nl_label
    global _system_situation_uris

    logger.info("[ontology-cache] Ontologie-data laden van Fuseki...")

    evidence_rows = await sparql_select_global(f"""
        PREFIX valor: <{VALOR_NS}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?uri ?label WHERE {{
          GRAPH <{_TESSERA_GRAPH}> {{
            ?uri a valor:EvidenceType ;
                 rdfs:label ?label .
            FILTER(lang(?label) = "en")
          }}
        }}
    """)
    _evidence_label_to_uri = {row["label"]: row["uri"] for row in evidence_rows}
    logger.info("[ontology-cache] Evidence types: %s", list(_evidence_label_to_uri.keys()))

    status_rows = await sparql_select_global(f"""
        PREFIX valor: <{VALOR_NS}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?uri ?label WHERE {{
          GRAPH <{_TESSERA_GRAPH}> {{
            ?uri a valor:EpistemicStatus ;
                 rdfs:label ?label .
            FILTER(lang(?label) = "en")
          }}
        }}
    """)
    _status_label_to_uri = {row["label"]: row["uri"] for row in status_rows}
    _status_uri_to_label = {v: k for k, v in _status_label_to_uri.items()}
    logger.info("[ontology-cache] Epistemic statuses: %s", list(_status_label_to_uri.keys()))

    nl_status_rows = await sparql_select_global(f"""
        PREFIX valor: <{VALOR_NS}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?uri ?label WHERE {{
          GRAPH <{_TESSERA_GRAPH}> {{
            ?uri a valor:EpistemicStatus ;
                 rdfs:label ?label .
            FILTER(lang(?label) = "nl")
          }}
        }}
    """)
    _status_uri_to_nl_label = {row["uri"]: row["label"] for row in nl_status_rows}
    logger.info("[ontology-cache] Epistemic statuses (nl): %s", list(_status_uri_to_nl_label.values()))

    transition_rows = await sparql_select_global(f"""
        PREFIX valor: <{VALOR_NS}>
        SELECT ?from ?to WHERE {{
          GRAPH <{_TESSERA_GRAPH}> {{
            ?from valor:allowedTransitionTo ?to .
          }}
        }}
    """)
    _valid_transitions = {}
    for row in transition_rows:
        from_label = _status_uri_to_label.get(row["from"], row["from"])
        to_label = _status_uri_to_label.get(row["to"], row["to"])
        _valid_transitions.setdefault(from_label, set()).add(to_label)
    logger.info("[ontology-cache] Transities: %s", {k: list(v) for k, v in _valid_transitions.items()})

    req_rows = await sparql_select_global(f"""
        PREFIX valor: <{VALOR_NS}>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT ?uri WHERE {{
          GRAPH <{_TESSERA_GRAPH}> {{
            ?uri valor:requiresDecisionEpisode "true"^^xsd:boolean .
          }}
        }}
    """)
    _requires_decision_episode = {row["uri"] for row in req_rows}
    logger.info("[ontology-cache] Vereist DecisionEpisode: %s", _requires_decision_episode)

    # Argumentatierelaties (ObjectProperties met domain én range valor:Tessera)
    PREFIX_OWL = "http://www.w3.org/2002/07/owl#"
    argue_rows = await sparql_select_global(f"""
        PREFIX valor: <{VALOR_NS}>
        PREFIX owl:   <{PREFIX_OWL}>
        PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?uri ?label WHERE {{
          GRAPH <{_TESSERA_GRAPH}> {{
            ?uri a owl:ObjectProperty ;
                 rdfs:domain valor:Tessera ;
                 rdfs:range  valor:Tessera ;
                 rdfs:label ?label .
            FILTER(lang(?label) = "en")
          }}
        }}
    """)
    _argue_label_to_uri = {row["label"]: row["uri"] for row in argue_rows}
    logger.info("[ontology-cache] Argumentatierelaties: %s", list(_argue_label_to_uri.keys()))

    uncertainty_rows = await sparql_select_global(f"""
        PREFIX valor: <{VALOR_NS}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?uri ?label WHERE {{
          GRAPH <{_TESSERA_GRAPH}> {{
            ?uri a valor:UncertaintyLevel ;
                 rdfs:label ?label .
            FILTER(lang(?label) = "en")
          }}
        }}
    """)
    _uncertainty_label_to_uri = {row["label"]: row["uri"] for row in uncertainty_rows}
    logger.info("[ontology-cache] Uncertainty levels (PAMS): %s", list(_uncertainty_label_to_uri.keys()))

    APP_NS = f"{VALOR_NS}application#"
    APP_GRAPH = f"{VALOR_NS}application"
    role_rows = await sparql_select_global(f"""
        PREFIX app: <{APP_NS}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT ?uri ?label ?rbac ?weight ?voting WHERE {{
          GRAPH <{APP_GRAPH}> {{
            ?uri app:mapsToRBACRole ?rbac ;
                 app:roleWeight ?weight ;
                 app:hasVotingRight ?voting ;
                 rdfs:label ?label .
            FILTER(lang(?label) = "en")
          }}
        }}
    """)
    _participant_role_data = {}
    _rbac_role_weights = {}
    for row in role_rows:
        label = row["label"]
        rbac = row["rbac"]
        weight = int(row["weight"])
        voting = str(row["voting"]).lower() == "true"
        _participant_role_data[label] = {
            "uri": row["uri"],
            "rbac_role": rbac,
            "weight": weight,
            "voting_right": voting,
        }
        if rbac not in _rbac_role_weights or weight > _rbac_role_weights[rbac]:
            _rbac_role_weights[rbac] = weight
    logger.info("[ontology-cache] ParticipantRoles: %s", list(_participant_role_data.keys()))
    logger.info("[ontology-cache] RBAC gewichten: %s", _rbac_role_weights)

    disc_type_rows = await sparql_select_global(f"""
        PREFIX disc: <{VALOR_NS}disc#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?uri ?label WHERE {{
          GRAPH <{_DISC_GRAPH}> {{
            ?uri a disc:ContributionType ;
                 rdfs:label ?label .
            FILTER(lang(?label) = "nl")
          }}
        }}
    """)
    _disc_contribution_type_label_to_uri = {row["label"]: row["uri"] for row in disc_type_rows}
    logger.info("[ontology-cache] Bijdragetypes (disc): %s", list(_disc_contribution_type_label_to_uri.keys()))

    SYSONT_NS = f"{VALOR_NS}sysont#"
    SYSONT_GRAPH = f"{VALOR_NS}sysont"
    situation_rows = await sparql_select_global(f"""
        PREFIX sysont: <{SYSONT_NS}>
        SELECT ?uri WHERE {{
          GRAPH <{SYSONT_GRAPH}> {{
            ?uri a sysont:SystemSituation .
          }}
        }}
    """)
    _system_situation_uris = {row["uri"] for row in situation_rows}
    logger.info("[ontology-cache] SystemSituation instanties: %d geladen", len(_system_situation_uris))

    if not _evidence_label_to_uri or not _status_label_to_uri or not _valid_transitions:
        logger.warning(
            "[ontology-cache] Ontologie-cache onvolledig. "
            "Controleer of Fuseki draait en de tessera-module is geladen."
        )


def get_evidence_label_to_uri() -> dict[str, str]:
    return _evidence_label_to_uri


def get_status_label_to_uri() -> dict[str, str]:
    return _status_label_to_uri


def get_status_uri_to_label() -> dict[str, str]:
    return _status_uri_to_label


def get_valid_transitions() -> dict[str, set[str]]:
    return _valid_transitions


def requires_decision_episode(status_uri: str) -> bool:
    return status_uri in _requires_decision_episode


def get_argue_label_to_uri() -> dict[str, str]:
    return _argue_label_to_uri


def get_uncertainty_label_to_uri() -> dict[str, str]:
    return _uncertainty_label_to_uri


def get_shacl_shapes_graph() -> str:
    return _shacl_shapes_graph


def get_participant_role_data() -> dict[str, dict]:
    """label → {uri, rbac_role, weight, voting_right}"""
    return _participant_role_data


def get_rbac_role_weights() -> dict[str, int]:
    """rbac_role → max weight (derived from ontology ParticipantRole instances)"""
    return _rbac_role_weights


def has_voting_right(valor_role_label: str) -> bool:
    """True als de VALOR-O rol stemrecht heeft (uit ontologie)."""
    return _participant_role_data.get(valor_role_label, {}).get("voting_right", False)


def get_disc_contribution_type_label_to_uri() -> dict[str, str]:
    return _disc_contribution_type_label_to_uri


def get_system_situation_uris() -> set[str]:
    """Geeft de set van bekende sysont:SystemSituation URI's."""
    return _system_situation_uris


def get_epistemic_statuses() -> list[dict]:
    """Retourneert alle EpistemicStatus instanties met Engels en Nederlands label."""
    return [
        {"uri": uri, "label_en": label_en, "label_nl": _status_uri_to_nl_label.get(uri, label_en)}
        for label_en, uri in _status_label_to_uri.items()
    ]


def rbac_to_valor_role(rbac_role: str) -> str:
    """Geeft de primaire VALOR-O rol-label voor een Neo4j RBAC-rol.
    Kiest de rol met het hoogste gewicht als er meerdere mappen."""
    best_label = "Observer"
    best_weight = -1
    for label, data in _participant_role_data.items():
        if data["rbac_role"] == rbac_role and data["weight"] > best_weight:
            best_label = label
            best_weight = data["weight"]
    return best_label
