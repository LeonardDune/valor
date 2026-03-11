"""Startup cache van ontologie-gedreven validatiedata uit Fuseki.

Geladen bij applicatie-startup via load_ontology_cache().
Queryt de VALOR-O ontologie-graphs in Fuseki voor:
  - EvidenceType instanties (English label -> URI)
  - EpistemicStatus instanties (English label -> URI)
  - Geldige statusovergangen (valor:allowedTransitionTo)
  - Statussen die een DecisionEpisode vereisen (valor:requiresDecisionEpisode)
"""
import logging

from app.services.fuseki import sparql_select_global

logger = logging.getLogger(__name__)

_TESSERA_GRAPH = "https://valor-ecosystem.nl/ontology/tessera"
_VALOR_NS = "https://valor-ecosystem.nl/ontology/"

_evidence_label_to_uri: dict[str, str] = {}
_status_label_to_uri: dict[str, str] = {}
_status_uri_to_label: dict[str, str] = {}
_valid_transitions: dict[str, set[str]] = {}
_requires_decision_episode: set[str] = set()
_argue_label_to_uri: dict[str, str] = {}   # "undermines" → URI
_shacl_shapes_graph = "https://valor-ecosystem.nl/shacl/tessera"


async def load_ontology_cache() -> None:
    global _evidence_label_to_uri, _status_label_to_uri, _status_uri_to_label
    global _valid_transitions, _requires_decision_episode, _argue_label_to_uri

    logger.info("[ontology-cache] Ontologie-data laden van Fuseki...")

    evidence_rows = await sparql_select_global(f"""
        PREFIX valor: <{_VALOR_NS}>
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
        PREFIX valor: <{_VALOR_NS}>
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

    transition_rows = await sparql_select_global(f"""
        PREFIX valor: <{_VALOR_NS}>
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
        PREFIX valor: <{_VALOR_NS}>
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
        PREFIX valor: <{_VALOR_NS}>
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


def get_shacl_shapes_graph() -> str:
    return _shacl_shapes_graph
