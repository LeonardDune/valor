"""Migratiescript: Neo4j ConversationThreads → Fuseki disc:DiscussionThreads (US-16.7)

Migreert alle ConversationThreads die gekoppeld zijn aan FactorVersions of ClaimVersions
(d.w.z. Tesserae in het Fuseki-model) naar Fuseki als disc:DiscussionThread +
disc:ThreadContribution triples.

Het script is idempotent: threads met migrated_to_fuseki=true worden overgeslagen.
Na migratie wordt de Neo4j node gemarkeerd met migrated_to_fuseki: true.

Gebruik (vereist draaiende Neo4j + Fuseki):
    cd backend
    FUSEKI_URL=http://localhost:3030 python scripts/migrate_neo4j_threads_to_fuseki.py

    # Dry-run (geen schrijfoperaties):
    FUSEKI_URL=http://localhost:3030 python scripts/migrate_neo4j_threads_to_fuseki.py --dry-run
"""
import asyncio
import sys
import os
import argparse
import logging
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

DISC_NS = "https://valor-ecosystem.nl/ontology/disc#"
PROV_NS = "https://www.w3.org/ns/prov#"
XSD_NS = "http://www.w3.org/2001/XMLSchema#"
VALOR_NS = "https://valor-ecosystem.nl/ontology/"
RDFS_NS = "http://www.w3.org/2000/01/rdf-schema#"


# ---------------------------------------------------------------------------
# Neo4j helpers
# ---------------------------------------------------------------------------

def _get_unmigrated_threads(driver) -> list[dict]:
    """Geeft alle ConversationThreads die nog niet naar Fuseki zijn gemigreerd,
    inclusief hun FactorVersion/ClaimVersion doelknoop en bijbehorende DesignSpace."""
    query = """
    MATCH (s)-[:HAS_THREAD]->(t:ConversationThread)
    WHERE NOT t.migrated_to_fuseki = true
    AND (s:FactorVersion OR s:ClaimVersion)
    MATCH (ds:DesignSpace)<-[:HAS_DESIGN_SPACE]-(tv:ThemeVersion)-[rel]->(s)
    WHERE type(rel) IN ['HAS_FACTOR', 'HAS_CLAIM']
    OPTIONAL MATCH (creator:User)-[:AUTHORED]->(firstMsg:ConversationMessage)-[:BELONGS_TO]->(t)
    WITH t, s, ds, creator
    ORDER BY firstMsg.created_at ASC
    WITH t, s, ds, head(collect(creator)) AS first_creator
    RETURN
        t.id           AS thread_id,
        t.topic        AS topic,
        t.status       AS status,
        toString(t.created_at) AS created_at,
        s.id           AS target_id,
        labels(s)[0]   AS target_type,
        ds.id          AS design_space_id,
        coalesce(first_creator.id, '') AS creator_id
    ORDER BY t.created_at
    """
    with driver.session() as session:
        return [dict(r) for r in session.run(query)]


def _get_messages_for_thread(driver, thread_id: str) -> list[dict]:
    """Geeft alle berichten voor een thread, gesorteerd op aanmaaktijd."""
    query = """
    MATCH (m:ConversationMessage)-[:BELONGS_TO]->(t:ConversationThread {id: $tid})
    OPTIONAL MATCH (u:User)-[:AUTHORED]->(m)
    RETURN
        m.id                   AS msg_id,
        m.content              AS content,
        toString(m.created_at) AS created_at,
        coalesce(u.id, m.user_id, '') AS user_id
    ORDER BY m.created_at ASC
    """
    with driver.session() as session:
        return [dict(r) for r in session.run(query, {"tid": thread_id})]


def _mark_thread_migrated(driver, thread_id: str) -> None:
    """Markeert een ConversationThread als gemigreerd naar Fuseki."""
    query = """
    MATCH (t:ConversationThread {id: $tid})
    SET t.migrated_to_fuseki = true
    """
    with driver.session() as session:
        session.run(query, {"tid": thread_id})


def _count_fuseki_threads(loop, design_space_id: str) -> int:
    """Telt het aantal disc:DiscussionThreads in de named graph van een DesignSpace."""
    from app.services.fuseki import sparql_select
    query = f"SELECT (COUNT(?t) AS ?count) WHERE {{ ?t a <{DISC_NS}DiscussionThread> }}"
    rows = loop.run_until_complete(sparql_select(query, design_space_id))
    return int(rows[0]["count"]) if rows else 0


# ---------------------------------------------------------------------------
# Fuseki helpers
# ---------------------------------------------------------------------------

def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")


async def _get_default_contribution_type_uri() -> str:
    """Haalt de URI op van het standaard bijdragetype 'Observatie' uit de disc-ontologie."""
    from app.services.fuseki import sparql_select_global
    DISC_GRAPH = f"{VALOR_NS}disc"
    rows = await sparql_select_global(f"""
        PREFIX disc: <{DISC_NS}>
        PREFIX rdfs: <{RDFS_NS}>
        SELECT ?uri WHERE {{
          GRAPH <{DISC_GRAPH}> {{
            ?uri a disc:ContributionType ;
                 rdfs:label ?label .
            FILTER(lang(?label) = "nl" && str(?label) = "Observatie")
          }}
        }}
        LIMIT 1
    """)
    if rows:
        return rows[0]["uri"]
    # Fallback: eerste ContributionType
    rows = await sparql_select_global(f"""
        PREFIX disc: <{DISC_NS}>
        SELECT ?uri WHERE {{
          GRAPH <{VALOR_NS}disc> {{
            ?uri a disc:ContributionType .
          }}
        }}
        LIMIT 1
    """)
    return rows[0]["uri"] if rows else f"{DISC_NS}Observatie"


async def _thread_exists_in_fuseki(thread_id: str, design_space_id: str) -> bool:
    """Controleert of een disc:DiscussionThread al in Fuseki bestaat."""
    from app.services.fuseki import sparql_select
    thread_uri = f"urn:valor:thread:{thread_id}"
    rows = await sparql_select(
        f"ASK {{ <{thread_uri}> a <{DISC_NS}DiscussionThread> }}",
        design_space_id,
    )
    # sparql_select geeft een lege lijst terug bij false, anders een rij met 'true'
    # Gebruik COUNT als veilig alternatief
    count_rows = await sparql_select(
        f"SELECT (COUNT(*) AS ?c) WHERE {{ <{thread_uri}> a <{DISC_NS}DiscussionThread> }}",
        design_space_id,
    )
    return int(count_rows[0]["c"]) > 0 if count_rows else False


async def _insert_discussion_thread(
    thread_id: str,
    design_space_id: str,
    tessera_id: str,
    user_id: str,
    title: str | None,
    created_at: str | None,
) -> None:
    """Schrijft een disc:DiscussionThread naar Fuseki (idempotent via FILTER NOT EXISTS)."""
    from app.services.fuseki import _UPDATE_ENDPOINT, _raise_for_fuseki_error, FUSEKI_ADMIN_PASSWORD, named_graph_uri
    import httpx

    thread_uri = f"urn:valor:thread:{thread_id}"
    tessera_uri = f"urn:valor:tessera:{tessera_id}"
    user_uri = f"urn:valor:user:{user_id}" if user_id else "urn:valor:user:unknown"
    ds_uri = f"urn:valor:ds:{design_space_id}"
    graph_uri = named_graph_uri(design_space_id)
    timestamp = created_at or datetime.now(timezone.utc).isoformat()

    title_triple = f'\n      <{RDFS_NS}label> "{_escape(title)}"@nl ;' if title else ""

    update = f"""PREFIX disc: <{DISC_NS}>
PREFIX prov: <{PROV_NS}>
PREFIX xsd:  <{XSD_NS}>
PREFIX valor: <{VALOR_NS}>
PREFIX rdfs: <{RDFS_NS}>

INSERT {{
  GRAPH <{graph_uri}> {{
    <{thread_uri}> a disc:DiscussionThread ;{title_triple}
      prov:wasStartedBy <{user_uri}> ;
      prov:startedAtTime "{timestamp}"^^xsd:dateTime ;
      disc:aboutTessera <{tessera_uri}> ;
      valor:inDesignSpace <{ds_uri}> .
  }}
}}
WHERE {{
  FILTER NOT EXISTS {{
    GRAPH <{graph_uri}> {{ <{thread_uri}> a disc:DiscussionThread }}
  }}
}}"""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            _UPDATE_ENDPOINT,
            data={"update": update},
            auth=("admin", FUSEKI_ADMIN_PASSWORD),
            timeout=30,
        )
    _raise_for_fuseki_error(response)


async def _insert_thread_contribution(
    thread_id: str,
    design_space_id: str,
    msg_id: str,
    user_id: str,
    content: str,
    contribution_type_uri: str,
    created_at: str | None,
) -> None:
    """Schrijft een disc:ThreadContribution naar Fuseki (idempotent via FILTER NOT EXISTS)."""
    from app.services.fuseki import _UPDATE_ENDPOINT, _raise_for_fuseki_error, FUSEKI_ADMIN_PASSWORD, named_graph_uri
    import httpx

    # Gebruik het Neo4j bericht-ID als contrib-ID voor traceerbaarheid
    contrib_uri = f"urn:valor:contrib:{msg_id}"
    thread_uri = f"urn:valor:thread:{thread_id}"
    user_uri = f"urn:valor:user:{user_id}" if user_id else "urn:valor:user:unknown"
    graph_uri = named_graph_uri(design_space_id)
    timestamp = created_at or datetime.now(timezone.utc).isoformat()

    escaped_content = _escape(content)

    update = f"""PREFIX disc: <{DISC_NS}>
PREFIX prov: <{PROV_NS}>
PREFIX xsd:  <{XSD_NS}>
PREFIX valor: <{VALOR_NS}>

INSERT {{
  GRAPH <{graph_uri}> {{
    <{contrib_uri}> a disc:ThreadContribution ;
      disc:contributionType <{contribution_type_uri}> ;
      valor:messageContent "{escaped_content}"@nl ;
      prov:wasAssociatedWith <{user_uri}> ;
      prov:endedAtTime "{timestamp}"^^xsd:dateTime .
    <{thread_uri}> disc:hasContribution <{contrib_uri}> .
  }}
}}
WHERE {{
  FILTER NOT EXISTS {{
    GRAPH <{graph_uri}> {{ <{contrib_uri}> a disc:ThreadContribution }}
  }}
}}"""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            _UPDATE_ENDPOINT,
            data={"update": update},
            auth=("admin", FUSEKI_ADMIN_PASSWORD),
            timeout=30,
        )
    _raise_for_fuseki_error(response)


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

async def _verify_thread_in_fuseki(thread_id: str, design_space_id: str, expected_contributions: int) -> bool:
    """Controleert of de thread en het juiste aantal bijdragen in Fuseki staan."""
    from app.services.fuseki import sparql_select

    thread_uri = f"urn:valor:thread:{thread_id}"

    thread_rows = await sparql_select(
        f"SELECT (COUNT(*) AS ?c) WHERE {{ <{thread_uri}> a <{DISC_NS}DiscussionThread> }}",
        design_space_id,
    )
    thread_ok = int(thread_rows[0]["c"]) == 1 if thread_rows else False

    contrib_rows = await sparql_select(
        f"SELECT (COUNT(?c) AS ?count) WHERE {{ <{thread_uri}> <{DISC_NS}hasContribution> ?c }}",
        design_space_id,
    )
    actual_contribs = int(contrib_rows[0]["count"]) if contrib_rows else 0
    contrib_ok = actual_contribs == expected_contributions

    ok = thread_ok and contrib_ok
    logger.info(
        "  Checksum thread %s: thread=%s bijdragen neo4j=%d fuseki=%d → %s",
        thread_id, "OK" if thread_ok else "MISSING",
        expected_contributions, actual_contribs, "OK" if ok else "MISMATCH",
    )
    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main(dry_run: bool) -> None:
    from app.db.utils import get_driver

    driver = get_driver()
    threads = _get_unmigrated_threads(driver)
    logger.info("Gevonden: %d niet-gemigreerde ConversationThreads", len(threads))

    if not threads:
        logger.info("Niets te migreren.")
        return

    default_contribution_type_uri = await _get_default_contribution_type_uri()
    logger.info("Standaard bijdragetype URI: %s", default_contribution_type_uri)

    total_threads = total_contribs = skipped = 0
    checksum_failures: list[str] = []

    for t in threads:
        thread_id = t["thread_id"]
        design_space_id = t["design_space_id"]
        tessera_id = t["target_id"]
        user_id = t["creator_id"] or "unknown"

        prefix = "[DRY-RUN]" if dry_run else "[MIGRATE]"

        messages = _get_messages_for_thread(driver, thread_id)
        logger.info(
            "%s Thread %s → DS %s | tessera=%s | %d berichten",
            prefix, thread_id, design_space_id, tessera_id, len(messages),
        )

        if not dry_run:
            await _insert_discussion_thread(
                thread_id=thread_id,
                design_space_id=design_space_id,
                tessera_id=tessera_id,
                user_id=user_id,
                title=t.get("topic"),
                created_at=t.get("created_at"),
            )

            for msg in messages:
                msg_user = msg["user_id"] or user_id
                await _insert_thread_contribution(
                    thread_id=thread_id,
                    design_space_id=design_space_id,
                    msg_id=msg["msg_id"],
                    user_id=msg_user,
                    content=msg["content"],
                    contribution_type_uri=default_contribution_type_uri,
                    created_at=msg.get("created_at"),
                )

            ok = await _verify_thread_in_fuseki(thread_id, design_space_id, len(messages))
            if ok:
                _mark_thread_migrated(driver, thread_id)
                total_threads += 1
                total_contribs += len(messages)
            else:
                checksum_failures.append(thread_id)
        else:
            total_threads += 1
            total_contribs += len(messages)

    logger.info(
        "\nResultaat: %d threads gemigreerd, %d overgeslagen | bijdragen=%d",
        total_threads, skipped, total_contribs,
    )
    if checksum_failures:
        logger.warning("CHECKSUM MISMATCH voor threads: %s — uvicorn start toch op", checksum_failures)
    else:
        logger.info("Alle checksums OK.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migreer Neo4j ConversationThreads naar Fuseki disc-model")
    parser.add_argument("--dry-run", action="store_true", help="Geen schrijfoperaties")
    args = parser.parse_args()

    if args.dry_run:
        logger.info("DRY-RUN modus — geen wijzigingen worden opgeslagen")

    try:
        asyncio.run(main(dry_run=args.dry_run))
    except Exception as exc:
        logger.error("Migratiescript afgebroken met fout: %s — uvicorn start toch op", exc)
        sys.exit(0)
