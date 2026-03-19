"""Fire-and-forget dual-write helpers voor Fuseki.

Fuseki-fouten worden gelogd als warning en blokkeren nooit de primaire response.
"""
import logging
from datetime import datetime, timezone

from app.ontology import VALOR_NS
from app.services.fuseki import named_graph_uri, sparql_update
from app.services.ontology_cache import get_argue_label_to_uri, get_status_label_to_uri

logger = logging.getLogger(__name__)

_XSD = "http://www.w3.org/2001/XMLSchema#"


async def try_write_factor(factor_id: str, name: str, theme_id: str, user_id: str) -> None:
    """Schrijft een Factor als Tessera naar Fuseki. Fouten worden gelogd als warning."""
    if not theme_id:
        return
    try:
        tessera_uri = f"urn:valor:tessera:{factor_id}"
        user_uri = f"urn:valor:user:{user_id}"
        graph_uri = named_graph_uri(theme_id)
        claimed_at = datetime.now(timezone.utc).isoformat()
        proposed_uri = get_status_label_to_uri().get("Proposed", f"{VALOR_NS}ProposedStatus")
        escaped_name = name.replace("\\", "\\\\").replace('"', '\\"')

        sparql = f"""PREFIX valor: <{VALOR_NS}>
PREFIX xsd: <{_XSD}>

INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{tessera_uri}> a valor:Tessera ;
      valor:claimContent "{escaped_name}"@nl ;
      valor:epistemicStatus <{proposed_uri}> ;
      valor:claimType "AsIs" ;
      valor:claimedBy <{user_uri}> ;
      valor:claimedAt "{claimed_at}"^^xsd:dateTime ;
      valor:inDesignSpace <{graph_uri}> .
  }}
}}"""
        await sparql_update(sparql, theme_id)
        logger.debug("Fuseki sync: factor %s → tessera %s", factor_id, tessera_uri)
    except Exception:
        logger.warning("Fuseki sync mislukt voor factor %s", factor_id, exc_info=True)


async def try_write_claim(
    claim_id: str,
    source_id: str,
    target_id: str,
    polarity: str,
    theme_id: str,
) -> None:
    """Schrijft een Claim als argumentatierelatie naar Fuseki. Fouten worden gelogd als warning."""
    if not theme_id:
        return
    try:
        relation_label = "supports" if polarity == "+" else "undermines"
        relation_uri = get_argue_label_to_uri().get(relation_label)
        if not relation_uri:
            logger.warning(
                "Fuseki sync: relatie '%s' niet in ontologie, claim %s niet gesynchroniseerd",
                relation_label, claim_id,
            )
            return

        source_uri = f"urn:valor:tessera:{source_id}"
        target_uri = f"urn:valor:tessera:{target_id}"
        graph_uri = named_graph_uri(theme_id)

        await sparql_update(
            f"""INSERT DATA {{
  GRAPH <{graph_uri}> {{
    <{source_uri}> <{relation_uri}> <{target_uri}> .
  }}
}}""",
            theme_id,
        )
        logger.debug("Fuseki sync: claim %s → %s -[%s]-> %s", claim_id, source_uri, relation_label, target_uri)
    except Exception:
        logger.warning("Fuseki sync mislukt voor claim %s", claim_id, exc_info=True)
